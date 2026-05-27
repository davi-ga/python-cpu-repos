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
        "Reactor of RequestLabel message: "
        + str(event["message"])
        + "; Enactment is "
        + str(event["enactment"])
    )

    labeled = {
        "orderID": event["message"]["orderID"],
        "address": event["message"]["address"],
        "label": str(uuid.uuid4()),
    }

    payload = {"type": "send", "to": "Packer", "message": labeled}

    payload = json.dumps(payload).encode("utf-8")
    print("Sending Labeled: {}".format(labeled))
    response = client.invoke(
        FunctionName="LabelerAdapter",
        InvocationType="Event",
        LogType="Tail",
        ClientContext="Amit",
        Payload=payload,
    )
    print(response)

    return {"statusCode": 200, "body": json.dumps("Reactor!")}
