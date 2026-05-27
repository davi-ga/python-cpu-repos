import json
import uuid
import logging
import boto3

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

client = boto3.client("lambda")


def lambda_handler(event, context):
    # TODO implement

    print(
        "Reactor of RequestWrapping message: "
        + str(event["message"])
        + "; Enactment is "
        + str(event["enactment"])
    )

    wrapped = {
        "orderID": event["message"]["orderID"],
        "itemID": event["message"]["itemID"],
        "item": event["message"]["item"],
    }

    if wrapped["item"] == "glass":
        wrapping = "bubblewrap"
    else:
        wrapping = "paper"

    wrapped["wrapping"] = wrapping

    payload = {"type": "send", "to": "Packer", "message": wrapped}

    payload = json.dumps(payload).encode("utf-8")
    print("Sending Wrapped: {}".format(wrapped))
    response = client.invoke(
        FunctionName="WrapperAdapter",
        InvocationType="Event",
        LogType="Tail",
        ClientContext="Amit",
        Payload=payload,
    )
    print(response)

    return {"statusCode": 200, "body": json.dumps("Reactor!")}
