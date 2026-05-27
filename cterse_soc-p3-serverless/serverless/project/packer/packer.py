import pos
import json
import yaml
import os

name = "Packer"

with open("logistics.json") as stream:
    protocol = json.load(stream)
with open(os.environ['CONFIG']) as conf:
    configuration = yaml.safe_load(conf)

adapter = pos.Adapter(name, protocol, configuration, 'PackerHistory')


@adapter.received(protocol['messages']['Wrapped'])
def Wrapped(message, enactment):
    print("Received Wrapped: {}".format(message))
    labeled_msg = next((m for m in enactment if m.get("label")), None)
    if labeled_msg:
        # send packed notification for item
        ok, msg = adapter.send("Merchant", {
            "orderID": message["orderID"],
            "itemID": message["itemID"],
            "wrapping": message["wrapping"],
            "label": labeled_msg["label"],
            "status": "packed"
        })
        if not ok:
            print(msg)


@adapter.received(protocol['messages']['Labeled'])
def Labeled(message, enactment):
    print("Received Labeled: {}".format(message))
    packed = [m for m in enactment if m.get('status')]
    unpacked = [m for m in enactment
                if m.get('itemID') and
                not any(p.get('itemID') == m['itemID'] for p in packed)]
    for m in unpacked:
        ok, msg = adapter.send("Merchant", {
            "orderID": m["orderID"],
            "itemID": m["itemID"],
            "wrapping": m["wrapping"],
            "label": message["label"],
            "status": "packed"
        })
        if not ok:
            print(msg)


@adapter.sent(protocol['messages']['Packed'])
def handlePacked(message, enactment):
    print("An item has been successfully packed: " + json.dumps(message))


def lambda_handler(event, context):
    return adapter.handler(event, context)
