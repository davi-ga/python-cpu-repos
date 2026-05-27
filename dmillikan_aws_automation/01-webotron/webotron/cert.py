# -*- code utf-8 -*-

"""Classes for AWS Certificate Manager"""
import boto3
from botocore.exceptions import ClientError
from pprint import pprint


class CertManager:
    """Manage an AWS Certificate"""

    def __init__(self, session):
        """Creates a CertManager object"""
        self.session = session
        self.client = self.session.client('acm', region_name='us-east-1')

    def get_certificate(self, website):
        """Find a Hosted Zone that Matches Domain Name"""

        acm_paginator = self.client.get_paginator('list_certificates')

        for page in acm_paginator.paginate(CertificateStatuses=['ISSUED']):
            for cert in page['CertificateSummaryList']:
                alt_names = self.client.describe_certificate(
                    CertificateArn=cert['CertificateArn'])['Certificate']['SubjectAlternativeNames']
                for name in alt_names:
                    if website == name:
                        return cert['CertificateArn']
                    elif name[0] == "*" and website.endswith(name[1:]):
                        return cert['CertificateArn']

        return None
