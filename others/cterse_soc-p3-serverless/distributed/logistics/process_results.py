import json
import argparse
from datetime import datetime
import statistics
import math

parser = argparse.ArgumentParser(
    description="Process agent history data dumped from DynammoDB"
)
parser.add_argument(
    "--file", "-f", type=str, required=True, help="path to history data"
)
args = parser.parse_args()

with open(args.file, "r") as stream:
    data = json.loads(stream.read())

history = {}
for item in data["Items"]:
    orderID = item["orderID"]["S"]
    enactment = history.get(orderID, [])
    enactment.append(item)
    history[orderID] = enactment

print("Total orders: {}".format(len(history)))

items = {}
orders = {}
messages = []
itemless = []
for h in history:
    orders[h] = [datetime.fromisoformat(m["_time"]["S"]) for m in history[h]]
    messages.extend(orders[h])
    if not any(m for m in history[h] if "itemID" in m):
        itemless.append(h)
    for m in history[h]:
        if m.get("itemID"):
            id = m["orderID"]["S"] + ":" + m["itemID"]["S"]
            enactment = items.get(id, [])
            enactment.append(m)
            items[id] = enactment
print("Total items: {}".format(len(items)))
complete = len(orders) - len(itemless)
print("Complete orders: {}".format(complete))
order_duration = (max(messages) - min(messages)).total_seconds()
print("Total order duration: {:.2f}s".format(order_duration))
order_durations = [
    (max(ms) - min(ms)).total_seconds() for ms in orders.values() if len(ms) > 1
]
print(
    "Mean order duration: {:.2f}s ({:.2f})".format(
        statistics.mean(order_durations), statistics.pstdev(order_durations)
    )
)
print("Order rate: {:.2f}".format(complete / order_duration))

durations = []
incomplete = 0
item_messages = []
for i, enactment in enumerate(items.values()):
    if not any(item for item in enactment if "status" in item):
        incomplete += 1
        # print(history[enactment[0]['orderID']["S"]])
        continue

    item_messages.extend([datetime.fromisoformat(m["_time"]["S"]) for m in enactment])
    req_label = next(item for item in enactment if "status" not in item)
    packed = next(item for item in enactment if "status" in item)
    start = datetime.fromisoformat(req_label["_time"]["S"])
    finish = datetime.fromisoformat(packed["_time"]["S"])
    durations.append((finish - start).total_seconds())

print("Complete enactments: {}".format(len(durations)))
print("Incomplete enactments: {}".format(incomplete))
print("Percentage complete: {:.2f}%".format(len(durations) / len(items.keys()) * 100))

mean = statistics.mean(durations)
pstdev = statistics.pstdev(durations)
minutes = math.floor(mean / 60)
seconds = math.floor(mean - minutes * 60)
print("Mean item duration: {}, pstdev: {:.2f}s".format(mean, pstdev))

item_duration = (max(item_messages) - min(item_messages)).total_seconds()
print("Item completion rate: {:.2f}".format(len(items) / item_duration))
