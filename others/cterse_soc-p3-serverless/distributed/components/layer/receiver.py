import json
import logging
import boto3
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client("lambda")

# Compute adapter function name from ROLE envar
# As such, there needs to be a separate function for each agent, unlike emitter
adapter = os.environ["ROLE"] + "Adapter"


def lambda_handler(event, context):
    print(event)
    message = json.loads(event["body"])
    payload = {"type": "receive", "message": message}
    payload = json.dumps(payload).encode("utf-8")
    print("Received message: {}".format(message))
    response = client.invoke(
        FunctionName=adapter,
        InvocationType="Event",
        LogType="Tail",
        ClientContext="Amit",
        Payload=payload,
    )
    print("Invoked: {}, response: {}".format(adapter, response))
    return {"statusCode": 200, "body": json.dumps("Message received!")}
