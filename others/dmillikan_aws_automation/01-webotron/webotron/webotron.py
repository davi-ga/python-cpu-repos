#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Deploy Websites with AWS 

    Webotron automates the process of deploying static websites to AWS S3
    - Configure S3
        - Create them
        - Set them up for static website hosting
        - Deploy local files to them
"""

import boto3
import botocore
import click
from botocore.exceptions import ClientError
from math import floor
from math import ceil

from webotron.bucket import BucketManager
from webotron.domain import DomainManager
from webotron.cert import CertManager
from webotron.cdn import CloudFrontManager
from webotron import util

from pprint import pprint

session = None
bucket_manager = None
domain_manager = None
cert_manager = None
cdn_manager = None
client = None

#######################################################################################################
#######################################################################################################
#######################################################################################################
@click.group()
@click.option('--profile', default=None, help="Use a given AWS profile")
def cli(profile):
    """Webotron Synchronizes Local Directories with S3"""
    global session, bucket_manager, client, domain_manager, cert_manager, cdn_manager
    session_cfg = {}

    if profile:
        session_cfg['profile_name'] = profile

    session = boto3.Session(**session_cfg)
    bucket_manager = BucketManager(session)
    domain_manager = DomainManager(session)
    cert_manager = CertManager(session)
    cdn_manager = CloudFrontManager(session)

    client = boto3.client('s3')
    
#######################################################################################################
#######################################################################################################
#######################################################################################################
@cli.group("domains")
def domains():
    """Commands for Domains"""
#######################################################################################################
@domains.command("setup")
@click.argument("domain")
@click.argument("bucket")
def setup_domain(domain, bucket):
    """Configure Domain to Bucket Mapping"""
    zone = domain_manager.get_hosted_zone(domain) \
        or domain_manager.create_hosted_zone(domain)
    bucket_name = ".".join([bucket , domain])
    s3_bucket = bucket_manager.init_bucket(bucket_name)
    bucket_url = bucket_manager.get_bucket_url(s3_bucket)
    region = util.get_region(bucket_manager.get_bucket_region(s3_bucket))
    
    record_set = domain_manager.create_s3_domain_record(s3_bucket, zone, region)
  
    print("\t"+("📣    ")*20+"\n")
    print("\t📣" + (" "*30) + "Route 53 Domain Setup Succesfully" + (" "*30) + " 📣\n")
    print("\t📣    Hosted Zone :    {0}".format(
        zone['Id']) + (" " * (73-len(zone['Id'])) + "📣\n"))
    print("\t📣    Bucket URL  :    {0}".format(
        bucket_url) + (" " * (73-len(bucket_url)) + "📣\n"))
    print("\t📣    Alias URL   :    {0}".format(
        record_set) + (" " * (73-len(record_set)) + "📣\n"))
    print("\t"+("📣    ")*20+"\n")
    print("🔱  "*40)
    return
#######################################################################################################
#######################################################################################################
#######################################################################################################
@cli.group("certs")
def certs():
    """Commands for Certificates"""
#######################################################################################################
@certs.command("list")
@click.argument("website")
def list_certs(website):
    """Returns All Certificates"""
    print(cert_manager.get_certificate(website))
    print("🔱  "*40)
    return
#######################################################################################################
#######################################################################################################
#######################################################################################################
@cli.group("cdn")
def cdn():
    """Commands for CloudFront Content Delivery Network"""
#######################################################################################################
@cdn.command("list")
@click.argument("website")
def list_distributions(website):
    """Returns All Distirbutions"""
    distribution = cdn_manager.lookup_distribution(website)
    print("\t" + ("⛅️    " * 21) + "\n")
    # print("\t" + "."*150)
    msg = ""
    if not distribution:
        msg = "CloudFront distribution does not exist for {0}".format(website)
    else:
        msg = "CloudFront distribution {0} is {1} for {2}".format(distribution['DomainName'], distribution['Status'], website)
        
    padding = 99 - len(msg)

    print("\t⛅️" + (" " * floor(padding/2)) +
          msg + (" " * ceil(padding/2)) + "⛅️\n")

    print("\t" + ("⛅️    " * 21))

    print("🔱  "*40)
    return
#######################################################################################################
@cdn.command("setup")
@click.argument("website")
def setup_distribution(website):
    """Creates Distribution"""
   
    bucket = bucket_manager.get_bucket(website)
    if not bucket.creation_date:
        print("\t" + ("☠️   ")*10 + "\n")
        print("\t☠️\tBucket Does Not Exist\t    ☠️\n")
        print("\t" + ("☠️   ")*10)
        print("🔱  "*40)
        return
    certificate = cert_manager.get_certificate(website)
    if not certificate:
        print("\t" + ("☠️   ")*10 + "\n")
        print("\t☠️     Certificate Does Not Exist    ☠️\n")
        print("\t" + ("☠️   ")*10)
        print("🔱  "*40)
        return
    zone = domain_manager.get_hosted_zone(website)
    if not zone:
        print("\t" + ("☠️   ")*10 + "\n")
        print("\t☠️     Route 53 Zone Does Not Exist    ☠️\n")
        print("\t" + ("☠️   ")*10)
        print("🔱  "*40)
        return
    dns = domain_manager.get_record_sets(zone, website)
    if not dns:
        print("\t" + ("☠️   ")*12 + "\n")
        print("\t☠️     Route 53 Record Set Does Not Exist    ☠️\n")
        print("\t" + ("☠️   ")*12)
        print("🔱  "*40)
        return
    cdn_manager.setup_distribution(website, bucket, certificate, dns)
    
    print("🔱  "*40)
    return
#######################################################################################################
@cdn.command("delete")
@click.argument("website")
def delete_distribution(website):
    """Deletes Distribution"""

    print("\t" + ("🌧    " * 21) + "\n")

    cdn_manager.disable_distribution(website)


    print("\t" + ("🌧    " * 21) + "\n")
    print("🔱  "*40)
#######################################################################################################
#######################################################################################################
#######################################################################################################
@cli.group("buckets")
def buckets():
    """Commands for Buckets"""
#######################################################################################################
@buckets.command("sync")
@click.argument("pathname", type=click.Path(exists=True))
@click.option("--delete", default=False, is_flag=True, help="Will remove files from bucket that do not exist locally")
@click.argument("bucketname")
def sync_path(pathname, bucketname, delete):
    """Synchronize Local Path to S3 Bucket"""
    bucket_manager.sync_path(pathname, bucketname, delete)

    print("🔱  "*40)
    return
#######################################################################################################
@buckets.command("list")
@click.option("--pattern", default=None, help="Will filter buckets starting with pattern")
def list_buckets(pattern):
    """List all s3 buckets \n
    Will filter buckets with pattern is provided"""

    buckets = []
    print("\t" + ("🗑    "*21)+"\n")
    if pattern:
        for b in bucket_manager.find_bucket(pattern, True):
            buckets.append(b)
    else:
        buckets = bucket_manager.all_buckets()
    for b in buckets:
        print("\t🗑    " + b.name + (" " * (95-len(b.name))) + "🗑\n")
   
    print("\t" + ("🗑    "*21))
    print("🔱  "*40)
    return
#######################################################################################################
@buckets.command("create")
@click.argument("name")
@click.option("--region", "region", default='us-east-1', help='Bucket Region')
@click.option("--public", "public", default=False, is_flag=True, help='Make Bucket Public')
@click.option("--website_domain", "website", default=None, help='Host Static Website from Bucket\nWill Append Domain to Bucket')
def create_bucket(name, public, region, website):
    """Create new s3 bucket"""

    print("\t" + ("🗑    "*21)+"\n")
    msg="Creating New Bucket Named {0}".format(name)

    print("\t🗑" + (" " * (floor((99-len(msg))/2))) +
          msg + (" " * (ceil((99-len(msg))/2))) + "🗑\n")
    if website:
        name = '.'.join([name, website])

    s3_bucket = bucket_manager.init_bucket(name, region)
    region = bucket_manager.get_bucket_region(s3_bucket)
    region_endpoint = util.get_region(region)
    if website:
        msg = "🌎    🌍    🌏    Bucket Will Host Static Website    🌎    🌍    🌏"
        print("\t🗑" + (" " * (floor((99-len(msg))/2))) +
              msg + (" " * (ceil((99-len(msg))/2))) + "🗑\n")
        public = False
        bucket_manager.give_public_access(s3_bucket)
        bucket_manager.host_website(s3_bucket, region)
        zone = domain_manager.create_hosted_zone(website)
        domain_manager.create_s3_domain_record(
            s3_bucket, zone, region_endpoint)
        dns = domain_manager.get_record_sets(zone, name)
        
        certificate = cert_manager.get_certificate(website)

        dist = cdn_manager.setup_distribution(website, s3_bucket, certificate, dns)

        domain_manager.create_cf_domain_record(zone,name,dist['DomainName'])
        
        msg = "You may browse your website at https://{0}".format(name)
        print("\t🌎" + (" " * (floor((99-len(msg))/2))) +
              msg + (" " * (ceil((99-len(msg))/2))) + "🌍\n")

    if public:
        bucket_manager.give_public_access(s3_bucket)
        msg = "🧨    🧨    🧨    Bucket Has Public Access    🧨    🧨    🧨"
        print("\t🗑" + (" " * (floor((99-len(msg))/2))) +
              msg + (" " * (ceil((99-len(msg))/2))) + "🗑\n")


    print("\t" + ("🗑    "*21))
    print("🔱  "*40)
    return
#######################################################################################################
@buckets.command("delete")
@click.argument("name")
@click.option("--pattern_match", "pattern_match", default=False, is_flag=True, help="Will filter buckets starting with pattern")
def delete_bucket(name, pattern_match):
    """Will empty and delete s3 bucket"""

    print("\t" + ("🚨    "*21)+"\n")

    if name in util.protected_buckets:
        print("\t" + ("💀    "*21)+"\n")
        msg = "Will not delete protected bucket {0}".format(name)
        msg = ("\t💀    💀    💀" + (" " * (floor((79-len(msg))/2))) +
               msg + (" " * (ceil((79-len(msg))/2))) + "💀    💀    💀\n")
        print(msg)
        print("\t" + ("💀    "*21)+"\n")


    else:
        if pattern_match:
            msg = "You are attempting to delete all buckets with name starting wtih {0}".format(
                name)
        else:
            msg = "You are attempting to delete bucket named {0}".format(
                name)
        msg = ("\t🚨    " + msg + (" " * (95-len(msg))) + "🚨\n")
        print(msg)

        msg = "Are You Sure (YES) : "
        msg = ("\t🚨    " + msg )
        confirm = input(msg)
        print(" ")

        if confirm == 'YES':
            if not name == "dmillikan-synology" and confirm == 'YES':
                msg = "I am deleting it all now"
                msg=("\t🚨    " + msg + (" " * (95-len(msg))) + "🚨\n")
                print(msg)
                bucket_manager.delete_bucket(
                    name, domain_manager, cdn_manager, pattern_match=pattern_match)
        else:
            msg = "Invalid confirmation"
            msg = ("\t🚨    🚨    🚨" + (" " * (floor((79-len(msg))/2))) +
                   msg + (" " * (ceil((79-len(msg))/2))) + "🚨    🚨    🚨\n")
            print(msg)
            msg = "You entered        : {0}".format(confirm)
            msg = ("\t🚨    " + msg + (" " * (95-len(msg))) + "🚨\n")
            print(msg)
            msg = "Will not delete bucket {0}".format(name)
            msg=("\t🚨    " + msg + (" " * (95-len(msg))) + "🚨\n")
            print(msg)


    print("\t" + ("🚨    "*21)+"\n")
    print("🔱  "*40)
    return
#######################################################################################################
@buckets.group("objects")
def objects():
    """Commands for Bucket Objects"""
#######################################################################################################
@objects.command("list")
@click.argument('bucket')
def list_bucket_objects(bucket):
    """List objects within s3 bucket"""

    print("\t" + ("📄    "*21)+"\n")
    for okey in bucket_manager.all_objects(bucket):
        # print("\t\t" + okey.key)
        print("\t📄    " + okey.key + (" " * (95-len(okey.key))) + "📄\n")
    print("\t" + ("📄    "*21))
    print("🔱  "*40)
    return
#######################################################################################################
#######################################################################################################
#######################################################################################################


if __name__ == '__main__':
    try:
        print("🔱  "*40)
        cli()

    except ClientError as e:
        print("ClientError:\n\t{0}".format(e))
    except TypeError as e:
        print("TypeError:\n\t{0}".format(e))
