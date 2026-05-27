from importlib.machinery import SourceFileLoader

tweet = SourceFileLoader("tweet", "./lib/tweet.py").load_module()


def handler(event, context):
    print("Delete subscription")
    tweet.delete_subscription(event["id_str"])
