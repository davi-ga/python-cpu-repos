"""
Helper functions for interacting with Twitter

Use Tweepy package for posting statuses
Handle Twitter Account Activity Api with requests directly
"""

import tweepy
import requests
from requests_oauthlib import OAuth1
import json
import re
import io
import os
import base64
import hmac
import hashlib

from dotenv import load_dotenv

load_dotenv()

consumer_key = os.getenv("CONSUMER_KEY")
consumer_secret = os.getenv("CONSUMER_SECRET")
access_token = os.getenv("ACCESS_TOKEN")
access_token_secret = os.getenv("ACCESS_TOKEN_SECRET")

gw_url = os.getenv("GW_URL")
sls_stage = os.getenv("SLS_STAGE")
webhook_path = os.getenv("WEBHOOK_PATH")

resource_url = "https://api.twitter.com/1.1/account_activity/all/"


auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_token, access_token_secret)
api = tweepy.API(auth)


def delete_my_statuses():
    """
    Delete my statuses seen in home timeline
    """
    bot_id = api.me().id
    statuses = api.home_timeline()
    for status in statuses:
        if status.user.id == bot_id:
            api.destroy_status(status.id)
            print("Deleted " + str(status.id))


def post_reply(img_output, color_hex, status):
    """
    Make a reply to the status with an image and colors in HEX

    Parameters
    ----------
    img_output: Image
        Image of palette colors.
    hex_colors: ndarray
        Palette colors in HEX values
    status: dict
        Status to which the function replies to
    
    Returns
    ------
    reply: Status
        Tweepy Status reply
    
    """

    update = "@" + status["user"]["screen_name"] + "\n" + " ".join(color_hex)
    img_file = io.BytesIO()
    img_output.save(img_file, format="png")
    return api.update_with_media(
        filename="palette.png",
        status=update,
        in_reply_to_status_id=status["id"],
        auto_populate_reply_metadata=True,
        file=img_file,
    )


def get_image_url(status):
    """
    Get image url from tweet status

    Parameters
    ----------
    status: Tweet
        Tweet status that mentions img2palette
    
    Returns
    ------
    image_url: str
        Image url
    
    """
    if "media" not in status["entities"]:
        raise ValueError("No photo in status")
    if len(status["entities"]["media"]) == 0:
        raise ValueError("No photo in status")
    if status["entities"]["media"][0]["type"] != "photo":
        raise ValueError("No photo in status")
    return status["entities"]["media"][0]["media_url"]


def get_k(status):
    """
    Get number of color palette from tweet status

    Parameters
    ----------
    status: Tweet
        Tweet status that mentions img2palette
    
    Returns
    ------
    k: int
        Number of color palette
    
    """
    match = re.search(r"\b\d+\b", status["text"])
    if match:
        return int(match.group())
    else:
        return None


def generate_response_token(crc_token):
    """
    Generate a response token to account activity API crc challenge

    Parameters
    ----------
    crc_token: str
        Challenge-Response Checks token
    
    Returns
    ------
    response_token: str
        sha256 hashed response token
    
    """
    key_bytes = bytes(consumer_secret, encoding="ascii")
    msg_bytes = bytes(crc_token, encoding="ascii")
    hash_digest = hmac.new(key_bytes, msg=msg_bytes, digestmod=hashlib.sha256).digest()
    return "sha256=" + base64.b64encode(hash_digest).decode(encoding="ascii")


def generate_crc_response(crc_token):
    """
    Generate a response to account activity API Challenge-Response Checks

    Parameters
    ----------
    crc_token: str
        Challenge-Response Checks token
    
    Returns
    ------
    response: dict
        API response
    
    """
    response_token = generate_response_token(crc_token)
    return {
        "statusCode": 200,
        "body": json.dumps({"response_token": response_token}),
    }


def get_bearer_token():
    """
    Get bearer token for authentication
    
    Returns
    ------
    access_token: str
        Bearer token
    
    """
    response = requests.post(
        "https://api.twitter.com/oauth2/token?grant_type=client_credentials",
        auth=requests.auth.HTTPBasicAuth(consumer_key, consumer_secret),
    )
    response.raise_for_status()
    return json.loads(response.content)["access_token"]


def make_webhook():
    """
    Make a Twitter Account Activity API webhook pointing to API Gateway
    
    Returns
    ------
    response: Reposnse
        Post webhook reposnse
    
    """
    url = resource_url + sls_stage + "/webhooks.json"
    print("url:", url)
    response = requests.post(
        url,
        params={"url": gw_url + "/" + webhook_path},
        auth=OAuth1(consumer_key, consumer_secret, access_token, access_token_secret),
    )
    print("status code: ", response.status_code)
    print("content: ", response.content)
    response.raise_for_status()
    return response


def get_webhook():
    """
    Get existing Twitter Account Activity API webhooks
    
    Returns
    ------
    response: Reposnse
        Get webhook reposnse
    
    """
    bearer_token = get_bearer_token()
    url = resource_url + sls_stage + "/webhooks.json"
    print("url:", url)
    response = requests.get(url, headers={"Authorization": "Bearer " + bearer_token})
    print("status code: ", response.status_code)
    print("content: ", response.content)
    response.raise_for_status()
    return response


def delete_webhook(id_str):
    """
    Delete a Twitter Account Activity API webhook
    
    Parameters
    ----------
    id_str: str
        Webhook ID
    
    Returns
    ------
    response: Reposnse
        Delete webhook reposnse
    
    """
    url = resource_url + sls_stage + "/webhooks/" + id_str + ".json"
    print("url:", url)
    response = requests.delete(
        url,
        auth=OAuth1(consumer_key, consumer_secret, access_token, access_token_secret),
    )
    print("status code: ", response.status_code)
    print("content: ", response.content)
    response.raise_for_status()
    return response


def make_subscription():
    """
    Make a Twitter Account Activity API subscription
    
    Returns
    ------
    response: Reposnse
        Post subscription reposnse
    
    """
    url = resource_url + sls_stage + "/subscriptions.json"
    print("url:", url)
    response = requests.post(
        url,
        auth=OAuth1(consumer_key, consumer_secret, access_token, access_token_secret),
    )
    print("status code: ", response.status_code)
    print("content: ", response.content)
    response.raise_for_status()
    return response


def get_subscription():
    """
    Get existing Twitter Account Activity API subscriptions
    
    Returns
    ------
    response: Reposnse
        Get subscription reposnse
    
    """
    bearer_token = get_bearer_token()
    url = resource_url + sls_stage + "/subscriptions/list.json"
    print("url:", url)
    response = requests.get(url, headers={"Authorization": "Bearer " + bearer_token})
    print("status code: ", response.status_code)
    print("content: ", response.content)
    response.raise_for_status()
    return response


def delete_subscription(id_str):
    """
    Delete a Twitter Account Activity API subscription
    
    Parameters
    ----------
    id_str: str
        Subscription ID
    
    Returns
    ------
    response: Reposnse
        Delete subscription reposnse
    
    """
    bearer_token = get_bearer_token()
    url = resource_url + sls_stage + "/subscriptions/" + id_str + ".json"
    print("url:", url)
    response = requests.delete(url, headers={"Authorization": "Bearer " + bearer_token})
    print("status code: ", response.status_code)
    print("content: ", response.content)
    response.raise_for_status()
    return response
