import json


def hello(event, context):
    print("Hi Serverless !!! This is 2nd  Update")

    return "Hello World Example"

    # Use this code if you don't use the http event with the LAMBDA-PROXY
    # integration
    """
    return {
        "message": "Go Serverless v1.0! Your function executed successfully!",
        "event": event
    }
    """
