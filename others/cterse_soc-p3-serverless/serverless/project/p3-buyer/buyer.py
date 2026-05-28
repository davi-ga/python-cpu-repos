import logging
import json
import os
import time

import yaml
import pos
import random

logger = logging.getLogger()
logger.setLevel(logging.INFO)

name = "Buyer"

with open("p3protocol.json") as stream:
    protocol = json.load(stream)
with open(os.environ['CONFIG']) as conf:
    configuration = yaml.safe_load(conf)

adapter = pos.Adapter(name, protocol, configuration, 'Buyer')


def translate_dynamo(obj):
    result = {}
    for k in obj:
        type = list(obj[k].keys())[0]
        if type == "N":
            result[k] = int(obj[k]["N"])
        else:
            result[k] = obj[k][type]
    return result


def send_quote(event, context):
    for record in event["Records"]:
        print(record)

        update = record.get('dynamodb', {}).get('NewImage')
        if not update:
            print("No updates: {}".format(record))
            return

        quote_req = translate_dynamo(update)

        # if quote_req["buyerName"] == "buyerB":
        #     print("Quote to be sent by Buyer B. Discarded by Buyer A")
        #     return

        print("Retrieved quote request info: {}".format(quote_req))

        msg_quote_req = {
            "requestId": quote_req["requestId"],
            "item": quote_req["item"],
            "buyerName": quote_req["buyerName"],
        }

        print(f"Sending quote request: {msg_quote_req}")
        ok, msg = adapter.send("Merchant", msg_quote_req)
        if not ok:
            print(f"Error sending quote request to Merchant: {msg}")


def lambda_handler(*args):
    return adapter.handler(*args)


@adapter.sent(protocol['messages']['RequestQuote'])
def sentQuoteRequest(message, enactment):
    print(f"Quote request sent {json.dumps(message)}")


@adapter.sent(protocol['messages']['Order'])
def sent_order(message, enactment):
    print(f"sentOrder {json.dumps(message)}")


@adapter.sent(protocol['messages']['Pay'])
def sentPayment(message, enactment):
    print(f"sentPayment {json.dumps(message)}")


@adapter.sent(protocol['messages']['CancelOrder'])
def cancelledOrder(message, enactment):
    print(f"cancelledOrder {json.dumps(message)}")


@adapter.received(protocol['messages']['SendQuote'])
def received_quote(message, enactment):
    print(f"receivedQuote: {json.dumps(message)}")

    # Buyer -> Merchant: Order[ in requestId, in amount, out orderId, in item, out address, in buyerName]

    order_id = random.randrange(1, 100000, 5)
    address = random.sample(['Raleigh', 'Gettysburg', 'Indiana'], 1)[0]

    msg_order = {
        "requestId": message["requestId"],
        "amount": message["amount"],
        "item": message["item"],
        "buyerName": message["buyerName"],
        "orderId": order_id,
        "address": address
    }

    ok, msg = adapter.send("Merchant", msg_order)
    if not ok:
        print(f"Error sending order to Merchant: {msg}")

    # Buyer -> Merchant: Pay[in requestId, in orderId, in amount, out paymentId, in item, in address, in buyerName]

    # print("Sleeping for 4 seconds...")
    # time.sleep(4)
    # print("Sleep complete.")

    payment_id = random.randrange(1, 100000, 5)
    msg_pay = {
        "requestId": message["requestId"],
        "orderId": order_id,
        "amount": message["amount"],
        "item": message["item"],
        "address": address,
        "buyerName": message["buyerName"],
        "paymentId": payment_id
    }

    ok, msg = adapter.send("Merchant", msg_pay)
    if not ok:
        print(f"Error sending payment to Merchant: {msg}")

    # cancellation enactment only for buyer B.
    # For buyer B, fire cancel order for even numbered request Ids
    if message["buyerName"] == 'buyerB' and int(message["requestId"]) % 2 == 0:
        cancel_id = random.randrange(1, 1000, 1)
        msg_cancel_order = {
            "requestId": message["requestId"],
            "orderId": order_id,
            "cancelId": cancel_id
        }

        print(f"Sending cancel order to merchant")
        ok, msg = adapter.send("Merchant", msg_cancel_order)
        if not ok:
            print(f"Error Sending cancel order to merchant: {msg}")


@adapter.received(protocol['messages']['SendShippedNotification'])
def received_shipped_notification(message, enactment):
    print(f"received_shipped_notification {json.dumps(message)}")


@adapter.received(protocol['messages']['RefundBuyerOnCancel'])
def received_cancel_refund(message, enactment):
    print(f"received_cancel_refund {json.dumps(message)}")


@adapter.received(protocol['messages']['SendDeliveryReminder'])
def received_delivery_reminder(message, enactment):
    print(f"received_delivery_reminder {json.dumps(message)}")


@adapter.received(protocol['messages']['SendDefectiveNotification'])
def received_defective_notification(message, enactment):
    print(f"received_defective_notification {json.dumps(message)}")


@adapter.received(protocol['messages']['SendDefectiveRefund'])
def received_defective_refund(message, enactment):
    print(f"received_defective_refund {json.dumps(message)}")

