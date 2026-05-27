import boto3
import os
import stat
from botocore.exceptions import ClientError

session_cfg = {}
session_cfg['profile_name'] = 'automation'
session_cfg['region_name'] = 'us-east-1'
session = boto3.Session(**session_cfg)

ec2 = session.resource('ec2')
ec2_client = session.client('ec2')

auto = session.client('autoscaling')

auto.describe_auto_scaling_groups()

auto.execute_policy(AutoScalingGroupName='Notifon Example',PolicyName='Scale Up')