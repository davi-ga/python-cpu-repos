import json
import boto3
from decimal import Decimal
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client("lambda")

name = "Merchant"


def translate_dynamo(obj):
    result = {}
    for k in obj:
        type = list(obj[k].keys())[0]
        if type == "N":
            result[k] = int(obj[k]["N"])
        else:
            result[k] = obj[k][type]
    return result


def get_order_proactor(event, context):
    """
    Handle a stream event from DynamoDB.
    Receives a newly submitted order from the customer, and sends RequestLabel and RequestWrapping messages.
    """
    for record in event["Records"]:
        print(record)
        update = record.get("dynamodb", {}).get("NewImage")
        if not update:
            print("No updates: {}".format(record))
            return
        order = translate_dynamo(update)

        print("Received order: {}".format(order))

        request_label = {"orderID": order["orderID"], "address": order["address"]}
        payload = {"type": "send", "to": "Labeler", "message": request_label}
        payload = json.dumps(payload).encode("utf-8")
        print("Sending RequestLabel: {}".format(request_label))
        response = client.invoke(
            FunctionName="MerchantAdapter",
            InvocationType="Event",
            LogType="Tail",
            ClientContext="Amit",
            Payload=payload,
        )
        print(response)

        for i, item in enumerate(order["items"].split(",")):
            request_wrapping = {
                "orderID": order["orderID"],
                "itemID": str(i),
                "item": item,
            }
            payload = {"type": "send", "to": "Wrapper", "message": request_wrapping}
            payload = json.dumps(payload).encode("utf-8")
            print("Sending RequestWrapping: {}".format(request_wrapping))
            response = client.invoke(
                FunctionName="MerchantAdapter",
                InvocationType="Event",
                LogType="Tail",
                ClientContext="Amit",
                Payload=payload,
            )
            print(response)
