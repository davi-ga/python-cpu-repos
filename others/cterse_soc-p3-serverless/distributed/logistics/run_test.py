import argparse
import hashlib
import random
import time
from requests_futures.sessions import FuturesSession

session = FuturesSession(max_workers=10)

parser = argparse.ArgumentParser(
    description="Generate and monitor test data for Pelmeni."
)
parser.add_argument(
    "--target", "-t", type=str, help="target API for submitting test POs"
)
parser.add_argument("--number", "-n", type=int, help="number of POs to generate")
args = parser.parse_args()

items = ["ball", "bat", "plate", "glass"]
locations = ["Lancaster", "Raleigh", "London", "New York"]


def _main():
    rs = []
    for i in range(args.number):
        orderID = hashlib.sha256(str(time.time()).encode()).hexdigest()[:10]

        PO = {
            "orderID": orderID,
            "items": ",".join(random.sample(items, random.randint(1, 4))),
            "address": random.sample(locations, 1)[0],
        }

        # time.sleep(0.25)
        print("Submitting PO: {}".format(PO))
        rs.append(session.post(args.target, json=PO))
    print([r.result().status_code for r in rs])


if __name__ == "__main__":
    _main()
