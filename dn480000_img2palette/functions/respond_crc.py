from importlib.machinery import SourceFileLoader

tweet = SourceFileLoader("tweet", "./lib/tweet.py").load_module()


def handler(event, context):
    crc_token = event["queryStringParameters"]["crc_token"]
    return tweet.generate_crc_response(crc_token)
