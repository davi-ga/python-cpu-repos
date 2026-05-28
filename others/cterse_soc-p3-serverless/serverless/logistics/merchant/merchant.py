import pos
import json
import yaml
from decimal import Decimal
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

name = "Merchant"

with open("logistics.json") as stream:
    protocol = json.load(stream)
with open(os.environ['CONFIG']) as conf:
    configuration = yaml.safe_load(conf)

adapter = pos.Adapter(name, protocol, configuration, 'MerchantHistory')


def translate_dynamo(obj):
    result = {}
    for k in obj:
        type = list(obj[k].keys())[0]
        if type == "N":
            result[k] = int(obj[k]["N"])
        else:
            result[k] = obj[k][type]
    return result


def handle_order(event, context):
    """
    Handle a stream event from DynamoDB.
    Receives a newly submitted order from the customer, and sends RequestLabel and RequestWrapping messages.
    """
    for record in event["Records"]:
        print(record)
        update = record.get('dynamodb', {}).get('NewImage')
        if not update:
            print("No updates: {}".format(record))
            return
        order = translate_dynamo(update)

        print("Received order: {}".format(order))
        request_label = {
            "orderID": order["orderID"],
            "address": order["address"]
        }
        print("Sending RequestLabel: {}".format(request_label))
        ok, msg = adapter.send("Labeler", request_label)
        if not ok:
            print(msg)

        for i, item in enumerate(order["items"].split(',')):
            request_wrapping = {
                "orderID": order["orderID"],
                "itemID": i,
                "item": item
            }
            print("Sending RequestWrapping: {}".format(request_wrapping))
            ok, msg = adapter.send("Wrapper", request_wrapping)
            if not ok:
                print(msg)


@adapter.sent(protocol['messages']['RequestLabel'])
def handleRequestLabel(message, enactment):
    logger.info("RequestLabel sent: " + json.dumps(message))


@adapter.sent(protocol['messages']['RequestWrapping'])
def handleRequestWrapping(message, enactment):
    logger.info("RequestWrapping sent: " + json.dumps(message))


@adapter.received(protocol['messages']['Packed'])
def handlePacked(message, enactment):
    logger.info("An item has been successfully packed: " +
                json.dumps(message))


def lambda_handler(*args):
    return adapter.handler(*args)
