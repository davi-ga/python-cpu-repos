import boto3
from pathlib import Path


session = boto3.Session(profile_name='automation')

s3 = session.resource('s3')
s3.create_bucket(Bucket='py3lab.dmillikan.com')
bucket = s3.Bucket('py3lab.dmillikan.com')
pathname = '/Users/danielmillikan/Downloads/Pexels Videos 2430839.mp4'
p = Path(pathname)
bucket.upload_file(pathname, p.name)

rekognition_client = session.client('rekognition')

jobid = rekognition_client.start_label_detection(Video={'S3Object': {'Bucket': bucket.name, 'Name': p.name}})

resp = rekognition_client.get_label_detection(JobId=jobid['JobId'])


