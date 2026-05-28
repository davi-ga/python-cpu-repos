import urllib
from os import environ

token = environ.get("SLACK_ACCESS_TOKEN")
channel = environ.get("SLACK_CHANNEL")

def handler(event, context):
  message = event["slack_message"]
  url = "https://slack.com/api/chat.postMessage"

  data = urllib.parse.urlencode((
    ("token", token),
    ("channel", channel),
    ("text", message)
  )).encode("ascii")
  headers = {"Content-Type": "application/json"}

  try:
    print(f"Posting slack message to channel '{channel}' ...")
    request = urllib.request.Request(url, data, headers)
    urllib.request.urlopen(request)
    return True
  except Exception as error:
    raise Exception(f"Error posting to slack: {error}")
