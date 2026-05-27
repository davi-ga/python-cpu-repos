import pos
import os

name = "Wrapper"
logistics_dir = os.path.dirname(__file__)

db_dir = os.path.join(logistics_dir, "db")
db_path = os.path.join(db_dir, name+".db")

protocol_path = os.path.join(logistics_dir, "protocol.txt")
configuration_path = os.path.join(logistics_dir, "configuration.txt")

adapter = pos.Adapter(name, protocol_path, configuration_path, db_path)


@adapter.register_handler("RequestWrapping")
def Wrapped(message):  # need enactment parameter...
    "Handle Merchant -> Wrapper: RequestWrapping[in orderID key, out itemID key, out item]"

    item = message.parameters['item']

    # wrap durable items in paper, which is cheaper
    parameters['wrapping'] = \
        'paper' if item in {'shoe', 'ball'} else 'bubblewrap'

    # send Wrapper -> Packer: Wrapped[in orderID key, in itemID key, in item, out wrapping]
    adapter.send("Wrapped", parameters)


if __name__ == '__main__':
    adapter.run()
