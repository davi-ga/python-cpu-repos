import logging
import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
import datetime
import threading
import sys
import os
import math

FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger("pos")

# Get role from environment, instead of hard-coding
ROLE = os.environ["ROLE"]

with open("/opt/logistics.json") as stream:
    protocol = json.load(stream)
with open(os.environ["CONFIG"]) as conf:
    configuration = json.load(conf)
with open("reactors.json") as react:
    reactors = json.load(react)


def now():
    return datetime.datetime.utcnow().isoformat()


def match_schema(schemas, message):
    for schema in schemas:
        # find schema with exactly the same parameters (except nils, which should not be bound)
        if (
            not set(schema["ins"])
            .union(schema["outs"])
            .symmetric_difference(message.keys())
        ):
            return schema


def check_integrity(message, enactment):
    """
    Make sure message is consistent with an enactment.
    Each message in enactment should have the same keys.

    Returns true if the parameters in the message are consistent with all messages in the enactment.
    """
    print("Checking integrity: {} in {}".format(message, enactment))
    # may not the most efficient algorithm for large histories
    # might be better to ask the database to find messages that don't match
    return all(message[p] == m[p] for p in message.keys() for m in enactment if p in m)


def check_outs(schema, enactment):
    """
    Make sure none of the outs have been bound.
    Only use this check if the message is being sent.
    """
    return not any(m.get(p) for m in enactment for p in schema["outs"])


class Adapter:
    def __init__(self, role, protocol, configuration, history_table_name):
        """
        Initialize the PoS adapter.

        role: name of the role being implemented
        protocol: a protocol specification
          {name, keys, messages: [{name, from, to, parameters, keys, ins, outs, nils}]}
        configuration: a dictionary of roles to endpoint URLs
          {role: url}
        history_table_name: the name of the DynamoDB table to use for storing message history
        """
        self.role = role
        self.protocol = protocol
        self.configuration = configuration
        self.sent_handlers = {}
        self.received_handlers = {}

        self.db = dynamo_table(history_table_name)

    def get_enactment(self, schema, message):
        """
        Get all of the messages that match the keys of a message, as specified by schema
        """
        logger.info("Getting enactment for schema: {}".format(schema))
        keys = schema["keys"]
        print("Keys are " + str(keys))
        # we're using the first key as the partition key
        key_exp = Key(keys[0]).eq(message[keys[0]])

        print(str(self.db))
        print("Key expression is " + str(key_exp))
        # any other keys are just attributes; need a filter expression
        if len(keys) > 1:
            f = None
            for k in keys[1:]:
                exp = Attr(k).not_exists() | Attr(k).eq(message[k])
                f = f & exp if f else exp

            response = self.db.query(
                KeyConditionExpression=key_exp, FilterExpression=f, ConsistentRead=True
            )
        else:
            response = self.db.query(
                KeyConditionExpression=key_exp, ConsistentRead=True
            )

        print("DB response is " + str(response))
        messages = response["Items"]
        for m in messages:
            m.pop("_time")  # _time not part of the message
            m.pop("_exp")  # _exp not part of the message
        return messages

    def get_schema(self, to, message):
        return match_schema(
            [
                schema
                for schema in self.protocol["messages"].values()
                if schema["to"] == to
            ],
            message,
        )

    def receive(self, message):
        schema = self.get_schema(self.role, message)
        if not schema:
            return {
                "statusCode": 500,
                "body": "Message does not match any schema: " + json.dumps(message),
            }

        enactment = self.get_enactment(schema, message)

        print("Checking for duplicates")
        if message in enactment:
            return {
                "statusCode": 200,
                "body": "Duplicate message " + json.dumps(message),
            }

        if not enactment or check_integrity(message, enactment):
            self.store(message)
            # self.handle_received_message(schema, message, enactment)
            print("Schema is " + str(schema))
            payload = {"message": message, "enactment": enactment}

            payload = json.dumps(payload).encode("utf-8")
            reactor = reactors.get(schema["name"])
            if reactor:
                response = client.invoke(
                    FunctionName=reactor,
                    InvocationType="Event",
                    LogType="Tail",
                    ClientContext="Amit",
                    Payload=payload,
                )
                print(response)

            return {"statusCode": 200, "body": json.dumps(message)}
        else:
            return {
                "statusCode": 500,
                "body": "Message does not satisfy integrity: " + json.dumps(message),
            }

    def handler(self, event, context):
        message = json.loads(event["body"])
        print("Received message: {}".format(message))
        return self.receive(message)

    def store(self, message):
        """Insert a message, represented as a dictionary
        E.g.: {"orderID": 1, "address": "Lancaster"}
        """
        message = message.copy()
        time = now()
        message["_time"] = time
        # set expiration time at 15min in the future
        message["_exp"] = math.floor(datetime.datetime.utcnow().timestamp()) + 15 * 60
        self.db.put_item(Item=message)
        return time

    def check_dependencies(self, schema, message):
        """
        Make sure that all 'in' parameters are bound and matched by some message in the history
        """
        for p in schema["ins"]:
            results = self.db.scan(
                Select="COUNT",
                FilterExpression=Attr(p).eq(message[p]),
                ConsistentRead=True,
            )
            if not results["Count"] > 0:
                return False
        return True

    def send(self, to, message):
        """
        Send a message by posting to the recipient's http endpoint,
        after checking for correctness, and storing the message.
        """
        print("Starting adapter.send().")
        schema = self.get_schema(to, message)
        print("Schema is " + str(schema))
        print("Message is " + str(message))
        if not schema:
            print("Message doesn't match any schema")
            return False, "Message doesn't match any schema"
        enactment = self.get_enactment(schema, message)
        print("Enactment is" + str(enactment))

        logger.info("Checking outs")
        if not check_outs(schema, enactment):
            print("Failed out check")
            return False, "Failed out check: {}".format(message)

        logger.info("Checking integrity")
        if not check_integrity(message, enactment):
            print("Failed integrity check")
            return False, "Failed integrity check: {}".format(message)

        logger.info("Checking dependencies")
        if not self.check_dependencies(schema, message):
            print("Failed dependency check")
            return False, "Failed dependency check: {}".format(message)

        logger.info("Storing message")
        self.store(message)
        # self.handle_sent_message(schema, message, enactment)
        print("Schema is " + str(schema))
        payload = {"message": message, "enactment": enactment}

        payload = json.dumps(payload).encode("utf-8")
        reactor = reactors.get(schema["name"])
        if reactor:
            logger.info("Invoking reactor: {}".format(reactor))
            response = client.invoke(
                FunctionName=reactor,
                InvocationType="Event",
                LogType="Tail",
                ClientContext="Amit",
                Payload=payload,
            )
            print(response)

        logger.debug("Sending message {} to {}".format(message, self.configuration[to]))
        print("Sending message to Emitter")

        payload = {"to": str(self.configuration[to]), "parameters": message}
        # requests.post(self.configuration[to],
        # json=message
        #
        payload = json.dumps(payload).encode("utf-8")
        response = client.invoke(
            FunctionName=ROLE + "Emitter",
            InvocationType="Event",
            LogType="Tail",
            ClientContext="Amit",
            Payload=payload,
        )
        print(response)

        return True, message

    def sent(self, schema):
        """
        Decorator for declaring sent message handlers.

        Example:
        @adapter.message(MessageSchema)
        def handle_message(message, enactment):
            'do stuff'
        """

        def register_handler(handler):
            self.sent_handlers[json.dumps(schema, separators=(",", ":"))] = handler

        return register_handler

    def received(self, schema):
        """
        Decorator for declaring received message handlers.

        Example:
        @adapter.message(MessageSchema)
        def handle_message(message, enactment):
            'do stuff'
        """

        def register_handler(handler):
            self.received_handlers[json.dumps(schema, separators=(",", ":"))] = handler

        return register_handler

    def handle_sent_message(self, schema, message, enactment):
        """
        Dispatch user-specified handler for schema, passing message and enactment.
        """
        handler = self.sent_handlers.get(json.dumps(schema, separators=(",", ":")))
        if handler:
            handler(message, enactment)

    def handle_received_message(self, schema, message, enactment):
        """
        Dispatch user-specified handler for schema, passing message and enactment.
        """
        handler = self.received_handlers.get(json.dumps(schema, separators=(",", ":")))
        if handler:
            handler(message, enactment)


#
# Code copied from aws.py
#


def offline():
    o = False
    print("Offline") if o else print("Online")
    return o


def lambda_client():
    endpoint_url = "http://localhost:3002/" if offline() else None
    return boto3.client("lambda", endpoint_url=endpoint_url)


def dynamo():
    endpoint_url = "http://localhost:8000/" if offline() else None
    dynamodb = boto3.resource("dynamodb", endpoint_url=endpoint_url)
    return dynamodb


def dynamo_client():
    endpoint_url = "http://localhost:8000/" if offline() else None
    client = boto3.client("dynamodb", endpoint_url=endpoint_url)
    return client


def dynamo_table(name):
    return dynamo().Table(name)


adapter = Adapter(ROLE, protocol, configuration, ROLE + "History")
client = boto3.client("lambda")


def lambda_handler(event, context):
    """
    Main entry-point.

    Event looks like this:
    {
      "to": "Labeler",
      "parameters": {"orderID": "1", "address": "Lancaster"}
    }
    """
    print("Event is" + str(event))
    if event["type"] == "send":
        adapter.send(event["to"], event["message"])
    elif event["type"] == "receive":
        adapter.receive(event["message"])
