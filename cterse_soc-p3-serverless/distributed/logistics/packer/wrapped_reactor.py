import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client("lambda")


def lambda_handler(event, context):
    # TODO implement

    print(
        "Reactor of Wrapped message: "
        + str(event["message"])
        + "; Enactment is "
        + str(event["enactment"])
    )
    message = event["message"]
    enactment = event["enactment"]
    labeled_msg = next((m for m in enactment if m.get("label")), None)
    if labeled_msg:
        # send packed notification for item
        payload = {
            "type": "send",
            "to": "Merchant",
            "message": {
                "orderID": message["orderID"],
                "itemID": message["itemID"],
                "wrapping": message["wrapping"],
                "label": labeled_msg["label"],
                "status": "packed",
            },
        }

        payload = json.dumps(payload).encode("utf-8")
        print("Sending Packed: {}".format(payload))
        response = client.invoke(
            FunctionName="PackerAdapter",
            InvocationType="Event",
            LogType="Tail",
            ClientContext="Amit",
            Payload=payload,
        )
        print(response)
