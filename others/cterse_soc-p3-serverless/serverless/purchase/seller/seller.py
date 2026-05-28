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
import uuid

logger = logging.getLogger()
logger.setLevel(logging.INFO)

name = "S"

with open("purchase.json") as stream:
    protocol = json.load(stream)
with open(os.environ['CONFIG']) as conf:
    configuration = yaml.safe_load(conf)

adapter = pos.Adapter(name, protocol, configuration, 'SellerHistory')


def translate_dynamo(obj):
    result = {}
    for k in obj:
        type = list(obj[k].keys())[0]
        if type == "N":
            result[k] = int(obj[k]["N"])
        else:
            result[k] = obj[k][type]
    return result


def handle_offer(event, context):
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
        offer = translate_dynamo(update)

        print("Found offer: {}".format(offer))
        offer_msg = {
            "ID": offer["offerID"],
            "prices": offer["prices"]
        }
        print("Sending Offer: {}".format(offer_msg))
        ok, msg = adapter.send("B", offer_msg)
        if not ok:
            print(msg)


@adapter.received(protocol['messages']['Buy'])
def handleBuy(message, enactment):
    logger.info("Buy received: " + json.dumps(message))
    item = None
    for m in enactment:
        item = m.get("item", item)
    adapter.send("B", {"ID": message["ID"], "item": item, "payment": message["payment"], "address": message["address"], "label": str(uuid.uuid4())})


@adapter.received(protocol['messages']['Rfq'])
def handleRfq(message, enactment):
    logger.info("Rfq received: " +
                json.dumps(message))
    adapter.send("B", {"ID": message["ID"], "item": message["item"], "price": "99.99"})


@adapter.received(protocol['messages']['Choose'])
def handleChoose(message, enactment):
    logger.info("Choose received: " +
                json.dumps(message))
    adapter.send("B", {"ID": message["ID"], "item": message["item"], "payment": message["payment"], "address": message["address"], "label": str(uuid.uuid4())})


@adapter.sent(protocol['messages']['Quote'])
def handleQuote(message, enactment):
    logger.info("Quote sent: " +
                json.dumps(message))


@adapter.sent(protocol['messages']['Offer'])
def handleOffer(message, enactment):
    logger.info("Offer sent: " +
                json.dumps(message))


@adapter.sent(protocol['messages']['Shipment'])
def handleShipment(message, enactment):
    logger.info("Shipment sent: " +
                json.dumps(message))


def lambda_handler(*args):
    return adapter.handler(*args)
