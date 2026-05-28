import requests
import os


def post_to_slack(event, context):
    slack_webhook_url = os.environ['SLACK_WEBHOOK_URL']
    
    slack_message = "At {time} an event of type {source} occured.\n{detail[Description]}".format(**event)
    data = {"text": slack_message}
    requests.post(slack_webhook_url, json=data)

    return
