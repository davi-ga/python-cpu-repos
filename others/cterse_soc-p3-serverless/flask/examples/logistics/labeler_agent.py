import uuid
import os
import pos

#####CONFIGURATIONS#####
name = "Labeler"
logistics_dir = os.path.dirname(__file__)

db_dir = os.path.join(logistics_dir, "db")
db_path = os.path.join(db_dir, name+".db")

protocol_path = os.path.join(logistics_dir, "protocol.txt")
configuration_path = os.path.join(logistics_dir, "configuration.txt")
adapter = pos.Adapter(name, protocol_path, configuration_path, db_path)
########################


@adapter.register_handler("RequestLabel")
# pass smth like a cursor, construct enactment object if asked. doesnt have to query until asked
def handleRequestLabel(message):
    print("RequestLabel message has been received from Merchant: " +
          str(message.parameters))
    label = uuid.uuid4()
    parameters = {
        "orderID": message.parameters["orderID"],
        "address": message.parameters["address"],
        "label": str(label)
    }
    adapter.send("Labeled", parameters)


@adapter.register_handler("Labeled")
# pass smth like a cursor, construct enactment object if asked. doesnt have to query until asked
def handleLabeled(message):
    print("Labeled message has been sent to Packer: " +
          str(message.parameters))  # < <--- dictionary of parameters


######################################################################################################
if __name__ == '__main__':
    adapter.app.run(host="127.0.0.2")
