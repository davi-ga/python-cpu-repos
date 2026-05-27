import boto3
import os
import stat
from botocore.exceptions import ClientError
from random import choices as choices
from ipaddress import ip_network
from ipaddress import ip_address

session_cfg = {}
session_cfg['profile_name'] = 'automation'
session_cfg['region_name'] = 'us-east-1'
session = boto3.Session(**session_cfg)

ec2 = session.resource('ec2')
ec2_client = boto3.client('ec2')


key_name = 'notifon_key'
ami_name = 'amzn2-ami-hvm-2.0.20190823.1-x86_64-gp2'
instance_type = 't3a.nano'
vpc_name = 'Lab Virginia' 
sec_group_name = 'MyWebDMZ'
curIp = '70.235.248.105'

key_path = key_name + '.pem'

key = ec2.KeyPair(key_name)

delKey = False
createKey = True
try:
    key_f = key.key_fingerprint
    try:
        with open(key_path,'r') as key_file:
            key_file.read()
            createKey = False
            delKey = False
            # print('Key {0} exists'.format(key_name))
    except os.error as e:
        if e.errno == 2:
            delKey = True
            createKey = True
        else:
            raise e
        


except ClientError as e:
    if e.response['Error']['Code'] == 'InvalidKeyPair.NotFound':
        createKey = True
    else:
        print(e.response['Error']['Code'])
        raise e

if delKey:
    # print('we need to delete the prior key')
    ec2_client.delete_key_pair(KeyName=key_name)

if createKey:
    # print('we need to create a new key')
    key = ec2.create_key_pair(KeyName=key_name)
    with open(key_path, 'w') as key_file:
        key_file.write(key.key_material)
        # print('Key {0} written to {1}'.format(key_name,key_path))
    

#change security for file
os.chmod(key_path, stat.S_IRUSR | stat.S_IWUSR)

#get the ami
filter = [{'Name': 'name', 'Values': [ami_name]}]
ami = list(ec2.images.filter(Owners=['amazon'], Filters=filter))[0]

#vpc = ec2.vpc(vpc_name)
vpcfilter = [{'Name': 'tag:Name', 'Values': [vpc_name]}]
vpcs = ec2.vpcs.filter(Filters=vpcfilter)
for v in vpcs:
    vpc = v

if not vpc:
    vpcfilter = [{'Name': 'isDefault', 'Values': ['true']}]
    vpcs = None
    vpcs = ec2.vpcs.filter(Filters=vpcfilter)
    for v in vpcs:
        vpc = v

#print('VPC ID         : {0}\nIs Default VPC : {1}\nHas CIDR Block : {2}'.format(vpc.id,vpc.is_default,vpc.cidr_block))

#get the subnets
pubvpcs = []
for s in vpc.subnets.all():
    # print("{0}\t{1}\t{2}".format(s.id,s.cidr_block,s.map_public_ip_on_launch))
    if s.map_public_ip_on_launch:
        pubvpcs.append(s.id)

if pubvpcs:
    subnet = choices(pubvpcs)
    # print('Selected Subnet ID : {0}'.format(subnet))


#get sec groups

for secgroup in vpc.security_groups.all():
    # print('Sec Group Name : {0}\nSec Group ID    : {1}'.format(secgroup.group_name,secgroup.id))
    if secgroup.group_name == sec_group_name:
        secgroupid = secgroup.id
    elif secgroup.group_name == 'default':
        defsecgrouid = secgroup.id

if not secgroupid:
    secgroupid = defsecgrouid


secgroup = ec2.SecurityGroup(secgroupid)

sshAllowed = False

for p in secgroup.ip_permissions:
    if p['FromPort'] == 22:
        for iprange in p['IpRanges']:
            ipn = ip_network(iprange['CidrIp'])
            if ip_address(curIp) in ipn:
               sshAllowed = True
               print(
                   "IP {0} is in network {1}".format(curIp, iprange))


if not sshAllowed:
    print('We will need to add ssh for ip {0} for security group {1}'.format(curIp,secgroup))
    response = secgroup.authorize_ingress(
        IpPermissions=[
            {
                'FromPort': 22,
                'ToPort': 22,
                'IpProtocol': 'TCP',
                'IpRanges': [{'CidrIp': '{0}/32'.format(curIp)}]
            }
        ]
    )
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        print('SSH Added')



# #create instance
instances = ec2.create_instances(
    ImageId = ami.id,
    InstanceType = instance_type,
    MinCount = 1,
    MaxCount = 1,
    KeyName = key_name,
    SubnetId = subnet[0],
    SecurityGroupIds=[secgroupid]
)

instance = instances[0]

instance.wait_until_running()
instance.reload()
# print('Instance IP is {0}'.format(instance.public_ip_address))
print('ssh -i {0} ec2-user@{1}'.format(key_path, instance.public_ip_address))



# instance.terminate()
