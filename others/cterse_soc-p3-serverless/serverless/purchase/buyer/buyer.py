"""
Purchase {
roles B, S
parameters out id key, out label, out item key
private price, payment, address, prices

B -> S: Rfq[out id key, out item]
S -> B: Quote[in id key, in item, out price]
B -> S: Buy[in id key, in price, out payment, out address]

S -> B: Offer[out id key, out prices]
B -> S: Choose[in id key, in prices, out item key, out payment, out address]

S -> B: Shipment[in id key, in item key, in payment, in address, out label]
}
"""

import pos
import json
import yaml
from decimal import Decimal
import os
import logging
import random

logger = logging.getLogger()
logger.setLevel(logging.INFO)

name = "B"

with open("purchase.json") as stream:
    protocol = json.load(stream)
with open(os.environ['CONFIG']) as conf:
    configuration = yaml.safe_load(conf)

adapter = pos.Adapter(name, protocol, configuration, 'BuyerHistory')


def translate_dynamo(obj):
    result = {}
    for k in obj:
        type = list(obj[k].keys())[0]
        if type == "N":
            result[k] = int(obj[k]["N"])
        else:
            result[k] = obj[k][type]
    return result


def handle_order(event, context):
    """
    Handle a stream event from DynamoDB.
    Receives a newly submitted order from the customer, and sends RequestLabel and RequestWrapping messages.
    """
    for record in event["Records"]:
        print(record)
        update = record.get('dynamodb', {}).get('NewImage')
        if not update:
            print("No updates: {}".format(record))
            return
        order = translate_dynamo(update)

        print("Received order: {}".format(order))
        rfq = {
            "ID": order["orderID"],
            "item": order["item"]
        }
        print("Sending rfq: {}".format(rfq))
        ok, msg = adapter.send("S", rfq)
        if not ok:
            print(msg)


@adapter.sent(protocol['messages']['Rfq'])
def handleRfq(message, enactment):
    logger.info("Rfq sent: " + json.dumps(message))

@adapter.sent(protocol['messages']['Buy'])
def handleBuy(message, enactment):
    logger.info("Buy message sent: " + json.dumps(message))

@adapter.sent(protocol['messages']['Choose'])
def handleChoose(message, enactment):
    logger.info("Choose message sent: " + json.dumps(message))


@adapter.received(protocol['messages']['Quote'])
def handleQuote(message, enactment):
    logger.info("Quote received: " +
                json.dumps(message))
    adapter.send("S", {"ID": message["ID"], "price": message["price"], "payment": "1000", "address": "Lancaster"})

@adapter.received(protocol['messages']['Offer'])
def handleOffer(message, enactment):
    logger.info("Offer received: " +
                json.dumps(message))
    #iterate through prices and choose an item
    prices = json.loads(message["prices"])
    for item in prices:
        if random.randint(0,1):
            logger.info("Buying item: " +
                        item)
            adapter.send("S", {"ID": message["ID"], "prices": message["prices"], "item": item, "payment": prices[item], "address": "Lancaster"})

@adapter.received(protocol['messages']['Shipment'])
def handleShipment(message, enactment):
    logger.info("Shipment received: " +
                json.dumps(message))


def lambda_handler(*args):
    return adapter.handler(*args)
