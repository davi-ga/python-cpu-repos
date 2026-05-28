#####CONFIGURATIONS#####
db_path = '/home/daria/Documents/test/test2'
from_ = "Labeler"
protocol_path="protocol.txt"
configuration_path="configuration.txt"
import pos
adapter= pos.Adapter(from_, protocol_path, configuration_path, db_path)

########################
import uuid

########################




@adapter.register_handler("RequestLabel")
def handleRequestLabel(message): #pass smth like a cursor, construct enactment object if asked. doesnt have to query until asked
	print("RequestLabel message has been received from Merchant: " + str(message.parameters))
	label = uuid.uuid4()
	parameters = {
	"orderID": message.parameters["orderID"],
	"address": message.parameters["address"],
	"label": str(label)
	}
	adapter.send("Labeled", parameters)


@adapter.register_handler("Labeled")
def handleLabeled(message): #pass smth like a cursor, construct enactment object if asked. doesnt have to query until asked
	print("Labeled message has been sent to Packer: " + str(message.parameters)) #< <--- dictionary of parameters


###############################################################################################################################
if __name__ == '__main__':
    adapter.app.run(host="127.0.0.2")
