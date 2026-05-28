import urllib

event = {'Records': [{'eventVersion': '2.1', 'eventSource': 'aws:s3', 'awsRegion': 'us-east-1', 'eventTime': '2019-09-11T14:58:31.905Z', 'eventName': 'ObjectCreated:Put', 'userIdentity': {'principalId': 'AWS:AIDAR6CP6ONYGVJMBHOI5'}, 'requestParameters': {'sourceIPAddress': '70.235.248.105'}, 'responseElements': {'x-amz-request-id': '4042C17E77A00C62', 'x-amz-id-2': 'mXUhmyp+NWkk/6KM1onG7pGW2x4ZpnHz2001nQwIEcaQMJcl9/B/ANEgbzJ+qtcX/SMSrIxB+84='},
                      's3': {'s3SchemaVersion': '1.0', 'configurationId': '2d4cdf81-2999-4537-9462-6de883e89516', 'bucket': {'name': 'dev.videolyzer.dmillikan.com', 'ownerIdentity': {'principalId': 'AX3IE4YX24QO5'}, 'arn': 'arn:aws:s3:::dev.videolyzer.dmillikan.com'}, 'object': {'key': 'Pexels+Videos+02.mp4', 'size': 3339235, 'eTag': '3151c4e476f0c28bdd90b57b35f4fdac', 'sequencer': '005D790B9739D5204A'}}}]}


event['Records'][0]['s3']['bucket']['name']

urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
