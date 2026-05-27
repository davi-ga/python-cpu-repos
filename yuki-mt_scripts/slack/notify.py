import json
import urllib.request

# how to create URL: https://api.slack.com/messaging/webhooks
webhook_url = ('https://hooks.slack.com/services/T84U83TA6/BJDRESBV1'
               '/1cFRnjN3BKgj8aqwWr0hEsjQ')
files = {'file': open("/mnt/c/Users/ymatoba/Downloads/example.png", 'rb')}
payload = {
    "channel": "#general",
    "username": "webhookbot",
    "icon_emoji": ":ghost:",
    'text': "<https://example.com|Overlook Hotel>\n:x: :ok: ",
    'filename': "filename",
}
# attachments, blocks:
# https://api.slack.com/messaging/webhook://api.slack.com/reference/messaging/attachments#fields
rich_payload = {
    "channel": "#general",
    "username": "webhookbot",
    "icon_emoji": ":ghost:",
    "attachments": [
        {
            "mrkdwn_in": ["text"],
            "color": "good",  # can be warning or danger
            "pretext": "Optional text that appears above the attachment block",
            "title": "title",
            "title_link": "https://api.slack.com/",
            "text": "Optional `text` that appears within the attachment",
            "fields": [
                {
                    "title": "A field's title",
                    "value": "This field's value",
                    "short": False
                },
            ],
        }
    ]
}
req = urllib.request.Request(webhook_url,
                             json.dumps(payload).encode(),
                             files=files)
with urllib.request.urlopen(req) as res:
    body = res.read()
