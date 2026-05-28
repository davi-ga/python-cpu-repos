import json
import logging
import os
import random
import pos
import yaml

logger = logging.getLogger()
logger.setLevel(logging.INFO)

name = "Shipper"

with open("p3protocol.json") as stream:
    protocol = json.load(stream)
with open(os.environ['CONFIG']) as conf:
    configuration = yaml.safe_load(conf)

adapter = pos.Adapter(name, protocol, configuration, 'Shipper')


def lambda_handler(*args):
    return adapter.handler(*args)


@adapter.received(protocol['messages']['SendItemToShip'])
def received_order(message, enactment):
    print(f"received_order: {json.dumps(message)}")

    # adapter.receive(message)

    # Shipper -> Buyer: Ship[ in requestId, in orderId, out shipmentId, in item]

    shipment_id = random.randrange(1, 100, 1)
    # msg_ship = {
    #     "requestId": message["requestId"],
    #     "orderId": message["orderId"],
    #     "item": message["item"],
    #     "shipmentId": shipment_id
    # }
    #
    # print(f"Shipping order to Buyer: {msg_ship}")
    # ok, msg = adapter.send("Buyer", msg_ship)
    # if not ok:
    #     print(f"Error Shipping order to Buyer: {msg}")
    #
    # # Shipper -> Merchant: ProvideTracking[ in requestId, in orderId, in shipmentId, out trackingId]
    #
    tracking_id = random.randrange(1, 100, 1)
    msg_provide_tracking = {
        "requestId": message["requestId"],
        "orderId": message["orderId"],
        "shipmentId": shipment_id,
        "trackingId": tracking_id
    }

    print(f"Sending tracking info to Merchant: {msg_provide_tracking}")
    ok, msg = adapter.send("Merchant", msg_provide_tracking)
    if not ok:
        print(f"Error Sending tracking info to Merchant: {msg}")

    if int(message["requestId"]) % 2 == 0:
        # send delivery success
        msg_confirm_del = {
            "requestId": message["requestId"],
            "orderId": message["orderId"],
            "shipmentId": shipment_id,
        }

        print(f"Sending delivery confirmation to Merchant: {msg_confirm_del}")
        ok, msg = adapter.send("Merchant", msg_confirm_del)
        if not ok:
            print(f"Error Sending delivery confirmation to Merchant: {msg}")
    else:
        # send defective item
        msg_def_item = {
            "requestId": message["requestId"],
            "orderId": message["orderId"],
            "shipmentId": shipment_id,
            "item": message["item"]
        }

        print(f"Sending defective notification to Merchant: {msg_def_item}")
        ok, msg = adapter.send("Merchant", msg_def_item)
        if not ok:
            print(f"Error Sending defective notification to Merchant: {msg}")


@adapter.sent(protocol['messages']['ProvideTracking'])
def tracking_info_sent(message, enactment):
    print(f"tracking_info_sent: {json.dumps(message)}")


@adapter.sent(protocol['messages']['ConfirmDelivery'])
def del_confirmation_sent(message, enactment):
    print(f"delivery_confirmation_sent: {json.dumps(message)}")


@adapter.sent(protocol['messages']['ReportItem'])
def defective_notification_sent(message, enactment):
    print(f"defective_notification_sent: {json.dumps(message)}")

