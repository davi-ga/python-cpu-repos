from importlib.machinery import SourceFileLoader

tweet = SourceFileLoader("tweet", "./lib/tweet.py").load_module()


def handler(event, context):
    print("Make webhook")
    tweet.make_webhook()
