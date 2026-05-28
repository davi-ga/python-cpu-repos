from .adapter import *
from .aws import dynamo, dynamo_client
import os
from boto3.dynamodb.conditions import Key, Attr
import pytest
import datetime
import responses
import json

os.environ["IS_OFFLINE"] = "True"

# This file is for testing the adapter with pytest

req_label_schema = {"name": "RequestLabel",
                    "from": "Merchant",
                    "to": "Labeler",
                    "keys": ["orderID"],
                    "parameters": ["orderID", "address"],
                    "outs": ["orderID", "address"],
                    "ins": [],
                    "nils": []}

labeled_schema = {"name": "Labeled",
                  "from": "Labeler",
                  "to": "Packer",
                  "keys": ["orderID"],
                  "parameters": ["orderID", "address", "label"],
                  "outs": ["label"],
                  "ins": ["orderID", "address"],
                  "nils": []}

req_wrapping_schema = {"name": "RequestWrapping",
                       "from": "Merchant",
                       "to": "Wrapper",
                       "keys": ["orderID", "itemID"],
                       "parameters": ["orderID", "itemID", "item"],
                       "outs": ["itemID", "item"],
                       "ins": ["orderID"],
                       "nils": []}

protocol = {
    "messages": {
        "RequestLabel": req_label_schema,
        "Labeled": labeled_schema,
    }
}

request_label_1 = {
    "orderID": 1,
    "address": "Lancaster"
}

labeled_1 = {
    "orderID": 1,
    "address": "Lancaster",
    "label": "random-label"
}

labeled_2 = {
    "orderID": 1,
    "address": "Wrong",
    "label": "random-label"
}

request_wrapping = {
}

configuration = {
    'Packer': 'http://packer.com/messages'
}

with open("logistics.json") as stream:
    logistics = json.load(stream)

adapter = Adapter('Labeler', protocol, configuration, 'LabelerHistory')


@pytest.fixture
def dynamodb():
    dynamodb = dynamo()
    table = dynamodb.create_table(
        TableName='LabelerHistory',
        KeySchema=[
            {
                'AttributeName': 'orderID',
                'KeyType': 'HASH'
            },
            {
                'AttributeName': '_time',
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'orderID',
                'AttributeType': 'N'
            },
            {
                'AttributeName': '_time',
                'AttributeType': 'S'
            },
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )

    # Wait until the table exists.
    table.meta.client.get_waiter('table_exists').wait(
        TableName='LabelerHistory')

    yield table

    print("Deleting table")
    table.delete()


def test_match_schema():
    assert match_schema(protocol["messages"].values(),
                        request_label_1) == req_label_schema
    assert match_schema(protocol["messages"].values(),
                        labeled_1) == labeled_schema


def test_match_schema_RequestWrapping():
    assert match_schema(logistics["messages"].values(), )


def test_check_integrity():
    assert check_integrity(labeled_1, [request_label_1])
    assert not check_integrity(labeled_2, [request_label_1])


def test_check_outs():
    assert check_outs(labeled_schema, [request_label_1])
    assert not check_outs(req_label_schema, [request_label_1])


def test_check_dependencies(dynamodb):
    assert adapter.check_dependencies(req_label_schema, request_label_1)
    assert not adapter.check_dependencies(labeled_schema, labeled_1)

    adapter.receive(request_label_1)
    assert adapter.check_dependencies(labeled_schema, labeled_1)


def test_dynamo(dynamodb):
    time = now()
    message = {**request_label_1, "_time": time}
    dynamodb.put_item(
        Item=message
    )

    response = dynamodb.get_item(
        Key={
            'orderID': 1,
            '_time': time
        })

    assert response['Item'] == message


def test_store(dynamodb):
    time = adapter.store(request_label_1)

    response = dynamodb.get_item(
        Key={
            'orderID': 1,
            '_time': time
        })

    assert response['Item'] == {**request_label_1, "_time": time}


def test_get_enactment(dynamodb):
    time = adapter.store(request_label_1)
    enactment = adapter.get_enactment(labeled_schema, labeled_1)
    assert {**request_label_1, "_time": time} in enactment


def test_get_enactment_multiple_keys(dynamodb):
    adapter.store(request_label_1)
    message = {
        "orderID": 1,
        "itemID": 1,
        "item": "ball"
    }
    assert len(adapter.get_enactment(labeled_schema, message)) == 1
    enactment = adapter.get_enactment(req_wrapping_schema, message)
    assert enactment


def test_get_schema():
    assert adapter.get_schema('Labeler', request_label_1) == req_label_schema
    assert adapter.get_schema('Packer', labeled_1) == labeled_schema


def test_receive(dynamodb):
    response = adapter.receive(request_label_1)
    assert response['statusCode'] == 200
    assert len(adapter.get_enactment(labeled_schema, labeled_1)) == 1


def test_receive_bogus(dynamodb):
    response = adapter.receive({"message": "bogus"})
    assert response['statusCode'] == 500
    assert "Message does not match any schema" in response['body']


def test_receive_integrity_violation(dynamodb):
    adapter.receive(request_label_1)
    response = adapter.receive({**request_label_1, "address": "wrong"})
    assert response['statusCode'] == 500
    assert 'Message does not satisfy integrity: ' in response['body']


def test_handler(dynamodb):
    event = {"body": json.dumps(request_label_1)}
    response = adapter.handler(event, {})
    assert response['statusCode'] == 200


@responses.activate
def test_send(dynamodb):
    responses.add(responses.POST, configuration['Packer'],
                  json={"statusCode": 200}
                  )
    adapter.receive(request_label_1)
    result = adapter.send("Packer", labeled_1)

    assert result[0] == True

    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == configuration['Packer']

    # shouldn't resend same message
    adapter.send("Packer", labeled_1)
    assert len(responses.calls) == 1


def test_send_bogus():
    result = adapter.send('Packer', {"message": "bogus"})
    assert result[0] == False
    assert result[1] == "Message doesn't match any schema"


def test_message():
    def labeled(message, enactment):
        pass

    adapter.message(labeled_schema)(labeled)

    assert len(adapter.handlers) > 0
    schema = json.dumps(labeled_schema, separators=(',', ':'))
    assert schema in adapter.handlers
    assert adapter.handlers[schema] == labeled


def test_handle_message():
    ms = []
    es = []

    @adapter.message(labeled_schema)
    def labeled(message, enactment):
        ms.append(message)
        es.append(enactment)

    e = ['a', 'b']
    adapter.handle_message(labeled_schema, 'test', e)

    assert 'test' in ms
    assert e in es
