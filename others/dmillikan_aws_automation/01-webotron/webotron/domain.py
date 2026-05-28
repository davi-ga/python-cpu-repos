# -*- code utf-8 -*-

import uuid
from webotron import util
import webotron.bucket
"""Classes for Route 53 Domains"""

class DomainManager:
    """Manage a Route 53 Domain"""

    def __init__(self,session):
        """Create a DomainManager Object"""
    
        self.session = session
        self.client = self.session.client('route53')

    def get_hosted_zone(self,domain_name):
        """Find a Hosted Zone that Matches Domain Name"""
        
        r53_paginator = self.client.get_paginator('list_hosted_zones')
        for page in r53_paginator.paginate():
            for zone in page['HostedZones']:
                if domain_name.endswith(zone['Name'][:-1]):
                    return zone
        
        return None   

    def create_hosted_zone(self,domain_name):
        """Create a Hosted Zone"""
        zone_name = '.'.join(domain_name.split('.')[-2:]) + '.'
        
        zone = self.get_hosted_zone(domain_name)

        if not zone:
            zone = self.client.create_hosted_zone(
                Name = zone_name,
                CallerReference = str(uuid.uuid4())
            )
        return zone

    def get_record_sets(self, zone, bucket_name):
        """Find a Hosted Zone that Matches Domain Name"""
        bucket_name = bucket_name + '.'
        r53_paginator = self.client.get_paginator('list_resource_record_sets')
        for page in r53_paginator.paginate(HostedZoneId=zone['Id']):
            for record in page['ResourceRecordSets']:
               if record['Name'] == bucket_name and record['Type'] == 'A':
                   return record

        return None

    def create_s3_domain_record(self,bucket,zone,region_endpoint):
        """Create S3 Domain Record"""
        
        # website_url = self.get_record_sets(zone, bucket.name)
        # if not website_url:
        response = self.client.change_resource_record_sets(
            HostedZoneId=zone['Id'],
            ChangeBatch={
                'Comment': 'Added by Webotron',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': bucket.name,
                            'Type': 'A',
                            'AliasTarget': {
                                'HostedZoneId': region_endpoint.hosted_zone,
                                'DNSName': region_endpoint.url,
                                'EvaluateTargetHealth': False
                            },
                        }
                    },
                ]
            }
        )['ResponseMetadata']['HTTPStatusCode']
        if response == 200:
            website_url = bucket.name
        # else:
        #     website_url = website_url['Name'][:-1]
        return "http://{0}".format(website_url)
                    

    def delete_s3_domain_record(self, bucket, zone):
        """Remove S3 Domain Record"""
               
        website_url = self.get_record_sets(zone, bucket.name)
        if website_url:
            # print(website_url['AliasTarget'])

            return self.client.change_resource_record_sets(
                HostedZoneId=zone['Id'],
                ChangeBatch={
                    'Comment': 'Removed by Webotron',
                    'Changes': [
                        {
                            'Action': 'DELETE',
                            'ResourceRecordSet': {
                                'Name': bucket.name,
                                'Type': 'A',
                                'AliasTarget': {
                                    'HostedZoneId': website_url['AliasTarget']['HostedZoneId'],
                                    'DNSName': website_url['AliasTarget']['DNSName'],
                                    'EvaluateTargetHealth': website_url['AliasTarget']['EvaluateTargetHealth']
                                },
                               
                            }
                        },
                    ]
                }
            )

        return 

    def create_cf_domain_record(self, zone, domain_name, cf_domain):
        """Create S3 Domain Record"""

        # website_url = self.get_record_sets(zone, bucket.name)
        # if not website_url:
        response = self.client.change_resource_record_sets(
            HostedZoneId=zone['Id'],
            ChangeBatch={
                'Comment': 'Added by Webotron',
                'Changes': [
                    {
                        'Action': 'UPSERT',
                        'ResourceRecordSet': {
                            'Name': domain_name,
                            'Type': 'A',
                            'AliasTarget': {
                                'HostedZoneId': 'Z2FDTNDATAQYW2',
                                'DNSName': cf_domain,
                                'EvaluateTargetHealth': False
                            },
                        }
                    },
                ]
            }
        )
        
        return response
