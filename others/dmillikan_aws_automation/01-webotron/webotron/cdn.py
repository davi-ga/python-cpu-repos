# -*- code utf-8 -*-

"""Classes for CloudFront"""
import boto3
from botocore.exceptions import ClientError
from pprint import pprint
from math import floor
from math import ceil
import uuid
from webotron.cert import CertManager
from webotron.bucket import BucketManager
from webotron.domain import DomainManager


class CloudFrontManager:
    """Manage CloudFront"""

    def __init__(self, session):
        """Creates a CertManager object"""
        self.session = session
        self.client = self.session.client('cloudfront')

    def lookup_distribution(self, website):
        """Find a CloudFront Distribution that Matches Domain Name"""

        cf_paginator = self.client.get_paginator('list_distributions')

        for page in cf_paginator.paginate():
            for dist in page['DistributionList']['Items']:
                for alias in dist['Aliases']['Items']:
                    if alias == website:
                        return dist

        return None

    def setup_distribution(self, website, bucket, certificate, dns):
        """Create a CloudFront Distribution for a Domain Name"""
        dist = self.lookup_distribution(bucket.name)
        if not dist:
            print("\t" + ("⛅️    " * 21)+"\n")
            print(
                '\t⛅️    We need to configure CloudFront for {0}'.format(website)+"\n")
            print("\t⛅️    Bucket         : " + bucket.name+"\n")
            print("\t⛅️    Certificate    : " + certificate+"\n")
            zone = dns['AliasTarget']['HostedZoneId']
            print("\t⛅️    Zone           : " + zone+"\n")

            origin_id = 'S3-' + website
            response = self.client.create_distribution(
                DistributionConfig={
                    'CallerReference': str(uuid.uuid4()),
                    'Aliases': {
                        'Quantity': 1,
                        'Items': [bucket.name]
                    },
                    'DefaultRootObject': 'index.html',
                    'Comment': 'Created by Webotron',
                    'Enabled': True,
                    'Origins': {
                        'Quantity': 1,
                        'Items': [
                            {
                                'Id': origin_id,
                                'DomainName': '{}.s3.amazonaws.com'.format(bucket.name),
                                'S3OriginConfig': {
                                    'OriginAccessIdentity': ''
                                }

                            }
                        ]
                    },
                    'DefaultCacheBehavior': {
                        'TargetOriginId': origin_id,
                        'ForwardedValues': {
                            'QueryString': True,
                            'Cookies': {'Forward': 'all'},
                            'Headers': {'Quantity': 0},
                            'QueryStringCacheKeys': {'Quantity': 0}
                        },
                        'TrustedSigners': {
                            'Enabled': False,
                            'Quantity': 0
                        },
                        'ViewerProtocolPolicy': 'redirect-to-https',
                        'SmoothStreaming': False,
                        'MinTTL': 3600,
                        'DefaultTTL': 86400,
                        'MaxTTL': 86400,
                        'Compress': False,
                    },
                    'ViewerCertificate': {
                        'CloudFrontDefaultCertificate': False,
                        'ACMCertificateArn': certificate,
                        'SSLSupportMethod': 'sni-only',
                        'MinimumProtocolVersion': 'TLSv1.1_2016',
                    }
                }
            )

            print("\t⛅️    CloudFront URL : " +
                  response['Distribution']['DomainName']+"\n")
            print("\t⛅️    Waiting for CloudFront to Deploy\n")
            waiter = self.client.get_waiter('distribution_deployed')
            waiter.wait(
                Id=response['Distribution']['Id'],
                WaiterConfig={
                    'Delay': 60,
                    'MaxAttempts': 60
                }
            )
            print("\t⛅️    CloudFront Deployed\n")
            print("\t" + ("⛅️    " * 21)+"\n")
            return(response['Distribution'])
        else:
            print("\t" + ("⛅️    " * 21)+"\n")
            msg = "CloudFront Already Configured for {0}".format(bucket.name)
            padding = 99 - len(msg)
            print("\t⛅️" + (" " * floor(padding/2)) +
                  msg + (" " * ceil(padding/2)) + "⛅️\n")
            print("\t" + ("⛅️    " * 21)+"\n")
            return dist



    def disable_distribution(self, website):
        """Delete a CloudFront Distribution for a Domain Name"""
        dist = self.lookup_distribution(website)
        if dist:
            curConfig = self.client.get_distribution_config(Id=dist['Id'])
          
            ETag = curConfig['ETag']
            DistConfg = curConfig['DistributionConfig']
            if DistConfg['Enabled']:
                msg = "Disabling CloudFront Distribution"
                padding = 99 - len(msg)
                print("\t🌧" + (" " * floor(padding/2)) +
                    msg + (" " * ceil(padding/2)) + "🌧\n")
                DistConfg['Enabled'] = False
                origin_id = dist['Origins']['Items'][0]['Id']

                response = self.client.update_distribution(
                    DistributionConfig=DistConfg,
                    Id=dist['Id'],
                    IfMatch=ETag
                )

                waiter = self.client.get_waiter('distribution_deployed')
                waiter.wait(
                    Id=dist['Id'],
                    WaiterConfig={
                        'Delay': 60,
                        'MaxAttempts': 60
                    }
            )
      
            else:
                msg = "CloudFront Distribution Not Enabled"
                padding = 99 - len(msg)
                print("\t🌧" + (" " * floor(padding/2)) +
                    msg + (" " * ceil(padding/2)) + "🌧\n")
            
            msg = "Deleting CloudFront Distribution"
            padding = 99 - len(msg)
            print("\t🌧" + (" " * floor(padding/2)) +
                  msg + (" " * ceil(padding/2)) + "🌧\n")
            curConfig = self.client.get_distribution_config(Id=dist['Id'])
            ETag = curConfig['ETag']
            self.client.delete_distribution(
                Id=dist['Id'],
                IfMatch=ETag
            )

            msg = "CloudFront Distribution Deleted"
            padding = 99 - len(msg)
            print("\t🌧" + (" " * floor(padding/2)) +
                  msg + (" " * ceil(padding/2)) + "🌧\n")
            print("\t" + ("⛅️    " * 21)+"\n")

        else:
            msg = "CloudFront Distribution Does Not Exists"
            padding = 99 - len(msg)
            print("\t🌧" + (" " * floor(padding/2)) +
                  msg + (" " * ceil(padding/2)) + "🌧\n")

        return
