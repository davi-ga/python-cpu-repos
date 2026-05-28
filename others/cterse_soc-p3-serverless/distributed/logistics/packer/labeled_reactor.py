import json
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

client = boto3.client("lambda")


def lambda_handler(event, context):
    # TODO implement

    print(
        "Reactor of Labeled message: "
        + str(event["message"])
        + "; Enactment is "
        + str(event["enactment"])
    )
    message = event["message"]
    enactment = event["enactment"]
    packed = [m for m in enactment if m.get("packed")]
    unpacked = [
        m
        for m in enactment
        if m.get("itemID") and not any(p.get("itemID") == m["itemID"] for p in packed)
    ]
    for m in unpacked:
        # send packed notification for item
        payload = {
            "type": "send",
            "to": "Merchant",
            "message": {
                "orderID": m["orderID"],
                "itemID": m["itemID"],
                "wrapping": m["wrapping"],
                "label": message["label"],
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
