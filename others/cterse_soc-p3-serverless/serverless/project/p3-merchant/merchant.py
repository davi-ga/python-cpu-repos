import json
import logging
import os

import boto3
import pos
import yaml
import random

logger = logging.getLogger()
logger.setLevel(logging.INFO)

name = "Merchant"

with open("p3protocol.json") as stream:
    protocol = json.load(stream)
with open(os.environ['CONFIG']) as conf:
    configuration = yaml.safe_load(conf)

adapter = pos.Adapter(name, protocol, configuration, 'Merchant')


def lambda_handler(*args):
    return adapter.handler(*args)


@adapter.received(protocol['messages']['RequestQuote'])
def get_quote_request(message, enactment):
    print(f"Quote request received: {json.dumps(message)}")

    amount = random.randrange(10, 1000, 100)
    quote_response = {
        "requestId": message["requestId"],
        "item": message["item"],
        "buyerName": message["buyerName"],
        "amount": amount
    }

    print(f"Sending quote response: {quote_response}")
    ok, msg = adapter.send("Buyer", quote_response)
    if not ok:
        print(f"Error sending quote response to Buyer: {msg}")


@adapter.received(protocol['messages']['Order'])
def received_order(message, enactment):
    print(f"received_order: {json.dumps(message)}")


@adapter.received(protocol['messages']['Pay'])
def received_pay(message, enactment):
    print(f"received_pay: {json.dumps(message)}")

    # Merchant -> Shipping: SendItemToShip[ in requestId, in orderId, in item, in address, in buyerName, in paymentId]

    msg_send_to_shipper = {
        "requestId": message["requestId"],
        "orderId": message["orderId"],
        "paymentId": message["paymentId"],
        "item": message["item"],
        "address": message["address"],
        "buyerName": message["buyerName"]
    }

    # Check if order cancelled before sending to ship
    order_cancelled = [m for m in enactment if m.get('cancelId')]
    if order_cancelled:
        print(f"Not processing the request/order anymore! {message}")
        return

    print(f"Sending order to shipper: {msg_send_to_shipper}")
    ok, msg = adapter.send("Shipper", msg_send_to_shipper)
    if not ok:
        print(f"Error sending order to Shipper: {msg}")


@adapter.received(protocol['messages']['CancelOrder'])
def received_cancel_order(message, enactment):
    print(f"received_cancel_order: {json.dumps(message)}")

@adapter.received(protocol['messages']['ProvideTracking'])
def received_tracking(message, enactment):
    print(f"received_tracking: {json.dumps(message)}")


@adapter.received(protocol['messages']['ConfirmDelivery'])
def received_del_confirmation(message, enactment):
    print(f"received_delivery_confirmation: {json.dumps(message)}")

    msg_del_notif = {
        "requestId": message["requestId"],
        "orderId": message["orderId"],
        "shipmentId": message["shipmentId"],
    }

    print(f"Sending delivery notification to Buyer: {msg_del_notif}")
    ok, msg = adapter.send("Buyer", msg_del_notif)
    if not ok:
        print(f"Error Sending delivery notification to Buyer: {msg}")


@adapter.received(protocol['messages']['ReportItem'])
def received_item_defective(message, enactment):
    print(f"received_item_defective: {json.dumps(message)}")

    msg_def_notif = {
        "requestId": message["requestId"],
        "orderId": message["orderId"],
        "shipmentId": message["shipmentId"],
        "item": message["item"]
    }

    print(f"Sending defective notification to Buyer: {msg_def_notif}")
    ok, msg = adapter.send("Buyer", msg_def_notif)
    if not ok:
        print(f"Error Sending defective notification to Buyer: {msg}")

    msg_def_refund = {
        "requestId": message["requestId"],
        "orderId": message["orderId"],
        "shipmentId": message["shipmentId"],
        "defectiveRefund": "Sending Defective Item Refund"
    }

    print(f"Sending defective refund to Buyer: {msg_def_refund}")
    ok, msg = adapter.send("Buyer", msg_def_refund)
    if not ok:
        print(f"Error Sending defective refund to Buyer: {msg}")


@adapter.sent(protocol['messages']['SendDefectiveRefund'])
def quote_response_sent(message, enactment):
    print(f"defective_refund_sent: {json.dumps(message)}")


@adapter.sent(protocol['messages']['SendQuote'])
def quote_response_sent(message, enactment):
    print(f"quote_response_sent: {json.dumps(message)}")


@adapter.sent(protocol['messages']['SendItemToShip'])
def item_to_ship_sent(message, enactment):
    print(f"item_to_ship_sent: {json.dumps(message)}")


@adapter.sent(protocol['messages']['SendShippedNotification'])
def shipped_notification_sent(message, enactment):
    print(f"shipped_notification_sent: {json.dumps(message)}")


@adapter.sent(protocol['messages']['RefundBuyerOnCancel'])
def cancel_refund_sent(message, enactment):
    print(f"cancel_refund_sent: {json.dumps(message)}")


@adapter.sent(protocol['messages']['SendDeliveryReminder'])
def del_reminder_sent(message, enactment):
    print(f"del_reminder_sent: {json.dumps(message)}")


@adapter.sent(protocol['messages']['SendDefectiveNotification'])
def defective_notification_sent(message, enactment):
    print(f"defective_notification_sent: {json.dumps(message)}")
