import pos
import json
import yaml
import os

name = "Wrapper"

with open("logistics.json") as stream:
    protocol = json.load(stream)
with open(os.environ['CONFIG']) as conf:
    configuration = yaml.safe_load(conf)

adapter = pos.Adapter(name, protocol, configuration, 'WrapperHistory')


@adapter.received(protocol['messages']['RequestWrapping'])
def handleRequestWrapping(message, enactment):
    print("RequestWrapping received: " + json.dumps(message))

    if message["item"] == "plate" or message["item"] == "glass":
        wrapping = "bubblewrap"
    else:
        wrapping = "paper"

    wrapped = {"orderID": message["orderID"],
               "itemID": message["itemID"],
               "item": message["item"],
               "wrapping": wrapping}
    ok, msg = adapter.send("Packer", wrapped)
    if not ok:
        print(msg)


@adapter.sent(protocol['messages']['Wrapped'])
def handleWrapped(message, enactment):
    print("Wrapped message has been sent: " + json.dumps(message))


def lambda_handler(*args):
    return adapter.handler(*args)
