import json
import logging
import requests
import boto3

FORMAT = "%(asctime)-15s %(message)s"
logging.basicConfig(format=FORMAT, level=logging.DEBUG)
logger = logging.getLogger("pos")

client = boto3.client("lambda")


def lambda_handler(event, context):
    print(event)
    response = requests.post(event["to"], json=event["parameters"])
    print(str(response.text))
    return {"statusCode": 200, "body": json.dumps("Message has been sent!")}
