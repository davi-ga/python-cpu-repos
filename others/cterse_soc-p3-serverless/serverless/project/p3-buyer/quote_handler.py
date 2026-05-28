import boto3
import json
from datetime import datetime

dynamodb = boto3.resource('dynamodb')

quotes_table = dynamodb.Table('Quotes')
# quotes_table = dynamodb.Table('Buyer')


def write_new_quote_request_to_dynamo(event, context):
    print('Generating new DynamoDB record')

    req_id = json.loads(event['body']).get('requestId')
    buyer = json.loads(event['body']).get('buyerName')
    item = json.loads(event['body']).get('item')
    item = item + "-" + str(req_id)

    db_entry = {
        "requestId": req_id,
        "item": item,
        "buyerName": buyer,
        "_time": str(datetime.now())
    }

    quotes_table.put_item(Item=db_entry)
    print(f"Added entry to Quotes table: {db_entry}")
    # print(f"Added entry to Buyer table: {db_entry}")

    response = {
        "statusCode": 200,
        "body": json.dumps(db_entry),
        "payload": "Successfully inserted quote request in Quotes table."
    }

    return response
