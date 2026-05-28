import json
import boto3
import os

if os.environ["IS_OFFLINE"] == "true":
    dynamodb = boto3.resource("dynamodb", endpoint_url="http://localhost:8000/")
else:
    dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table("Orders")

####################


def writeToDynamo(event, context):
    print("Generating new DynamoDB record")

    orderID = json.loads(event["body"]).get("orderID")
    address = json.loads(event["body"]).get("address")
    items = json.loads(event["body"]).get("items")

    entry = {"orderID": orderID, "address": address, "items": items}

    # Creating new record in DynamoDB table
    table.put_item(Item=entry)

    response = {"statusCode": 200, "body": json.dumps(entry)}

    return response
