import json
from importlib.machinery import SourceFileLoader

image = SourceFileLoader("image", "./lib/image.py").load_module()
tweet = SourceFileLoader("tweet", "./lib/tweet.py").load_module()


def respond_status(status):
    print("status id: ", status["id"])
    try:
        if "entities" not in status:
            raise ValueError("No mention in status")
        if "user_mentions" not in status["entities"]:
            raise ValueError("No mention in status")
        if len(status["entities"]["user_mentions"]) == 0:
            raise ValueError("No mention in status")
        my_id = tweet.api.me().id
        if status["user"]["id"] == my_id:
            raise ValueError("Status by myself")
        if not any([m["id"] == my_id for m in status["entities"]["user_mentions"]]):
            raise ValueError("Not mentioned in status")
        print("Mentioned in status")
        image_url = tweet.get_image_url(status)
        img_input = image.get_image_from_url(image_url)
        k = tweet.get_k(status)
        img_result, color_hex = image.get_palette(img_input, k)
        reply = tweet.post_reply(img_result, color_hex, status)
        print("Replied to ", status["id"], " with ", reply.id)
        return {
            "status_id": status["id"],
            "reply_id": reply.id,
        }
    except Exception as e:
        print("Did not reply to ", status["id"])
        return {
            "status_id": status["id"],
            "reason": str(e),
        }


def handler(event, context):
    body = json.loads(event["body"])
    print(body)
    if "tweet_create_events" in body:
        result = [respond_status(status) for status in body["tweet_create_events"]]
        print(result)
        return result
    else:
        return []
