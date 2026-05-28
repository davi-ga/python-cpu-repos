from importlib.machinery import SourceFileLoader

tweet = SourceFileLoader("tweet", "./lib/tweet.py").load_module()


def handler(event, context):
    tweet.delete_my_statuses()
