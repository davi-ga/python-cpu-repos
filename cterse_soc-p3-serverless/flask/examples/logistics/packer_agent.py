import pos
import os
name = "Packer"
logistics_dir = os.path.dirname(__file__)

db_dir = os.path.join(logistics_dir, "db")
db_path = os.path.join(db_dir, name+".db")

protocol_path = os.path.join(logistics_dir, "protocol.txt")
configuration_path = os.path.join(logistics_dir, "configuration.txt")

print(db_path)
adapter = pos.Adapter(name, protocol_path, configuration_path, db_path)

enactments = {}

####
# This agent is currently implemented like the PoT custom code,
# because the adapter does not yet handle correlation for the user. We
# don't actually have access to the rest of the enactment yet.
####


@adapter.register_handler("Wrapped")
def Wrapped(message):  # need enactment parameter...
    enactment = enactments.get(message.parameters["orderID"], {})
    items = enactment.get("items", [])
    items.append(message)
    if enactment["label"]:
        pack_item(message, enactment)


@adapter.register_handler("Labeled")
def Labeled(message):
    enactment = enactments.get(message.parameters["orderID"], {})
    enactment["label"] = message.parameters["label"]
    items = enactment.get("items", [])
    for item in items:
        pack_item(item, enactment)


def pack_item(item, enactment):
    if item.parameters["label"]:
        return  # don't pack an item twice...
    ps = item.parameters
    ps["label"] = enactment["label"]
    adapter.send("Packed", {
        "orderID": ps["orderID"],
        "itemID": ps["itemID"],
        "wrapping": ps["wrapping"],
        "label": ps["label"],
        "status": "packed"
    })


if __name__ == '__main__':
    adapter.run()
