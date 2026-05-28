import requests
url = ''
data = {"text": "Test from python"}
requests.post(url, json=data)
