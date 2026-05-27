import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client("lambda")


def lambda_handler(event, context):
    # TODO implement

    print(
        "Reactor of Packed message: "
        + str(event["message"])
        + "; Enactment is "
        + str(event["enactment"])
    )
