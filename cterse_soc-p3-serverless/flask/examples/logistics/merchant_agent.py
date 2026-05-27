import time
import sched
import sqlite3
import random
import os
import pos
from threading import Thread

##### CONFIGURATIONS #####
name = "Merchant"
logistics_dir = os.path.dirname(__file__)
protocol_path = os.path.join(logistics_dir, "protocol.txt")
configuration_path = os.path.join(logistics_dir, "configuration.txt")

db_dir = os.path.join(logistics_dir, "db")
history_db = os.path.join(db_dir, name+".db")
orders_db = os.path.join(db_dir, "orders.db")
adapter = pos.Adapter(name, protocol_path, configuration_path, history_db)
########################

connection = sqlite3.connect(orders_db)
cursor = connection.cursor()

last_id = -1
s = sched.scheduler(time.time, time.sleep)


def fetch_orders():
    print("Doing stuff...")
    # do your stuff
    global last_id
    query = "SELECT * FROM orders WHERE orderID>?"

    for row in cursor.execute(query, (str(last_id),)):

        orderID, address, items = row
        parameters = {
            "orderID": orderID,
            "address": address
        }

        adapter.send("RequestLabel", parameters)

        for itemID, item in enumerate(items.split(",")):
            parameters = {
                "orderID": orderID,
                "itemID": itemID,
                "item": item
            }
            adapter.send("RequestWrapping", parameters)

        last_id = orderID

    t = threading.Timer(0.5,fetch_orders).start()


fetch_orders()




@adapter.register_handler("RequestLabel")
# pass smth like a cursor, construct enactment object if asked. doesnt have to query until asked
def handleRequestLabel(message):
    # < <--- dictionary of parameters
    print("RequestLabel sent: " + str(message.parameters))


@adapter.register_handler("RequestWrapping")
# pass smth like a cursor, construct enactment object if asked. doesnt have to query until asked
def handleRequestWrapping(message):
    # < <--- dictionary of parameters
    print("RequestWrapping sent: " + str(message.parameters))


@adapter.register_handler("Packed")
# pass smth like a cursor, construct enactment object if asked. doesnt have to query until asked
def handlePacked(message):
    print("An item has been successfully packed: " +
          str(message.parameters))  # < <--- dictionary of parameters


if __name__ == '__main__':
    adapter.run()
