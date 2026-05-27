from collections import namedtuple

s3_endpoint = namedtuple('s3_endpoint',  ['region_name', 'url', 'hosted_zone'])

region_endpoint = {
    'us-east-2': s3_endpoint('US East(Ohio)',
                             's3-website.us-east-2.amazonaws.com', 'Z2O1EMRO9K5GLX'),
    'us-east-1': s3_endpoint('US East(N. Virginia)',
                             's3-website-us-east-1.amazonaws.com', 'Z3AQBSTGFYJSTF'),
    'us-west-1': s3_endpoint('US West(N. California)',
                             's3-website-us-west-1.amazonaws.com', 'Z2F56UZL2M1ACD'),
    'us-west-2': s3_endpoint('US West(Oregon)',
                             's3-website-us-west-2.amazonaws.com', 'Z3BJ6K6RIION7M'),
    'ap-east-1': s3_endpoint('Asia Pacific(Hong Kong)',
                             's3-website.ap-east-1.amazonaws.com', 'ZNB98KWMFR0R6'),
    'ap-south-1': s3_endpoint('Asia Pacific(Mumbai)',
                              's3-website.ap-south-1.amazonaws.com', 'Z11RGJOFQNVJUP'),
    'ap-northeast-3': s3_endpoint('Asia Pacific(Osaka-Local)',
                                  's3-website.ap-northeast-3.amazonaws.com', 'Z2YQB5RD63NC85'),
    'ap-northeast-2': s3_endpoint('Asia Pacific(Seoul)',
                                  's3-website.ap-northeast-2.amazonaws.com', 'Z3W03O7B5YMIYP'),
    'ap-southeast-1': s3_endpoint('Asia Pacific(Singapore)',
                                  's3-website-ap-southeast-1.amazonaws.com', 'Z3O0J2DXBE1FTB'),
    'ap-southeast-2': s3_endpoint('Asia Pacific(Sydney)',
                                  's3-website-ap-southeast-2.amazonaws.com', 'Z1WCIGYICN2BYD'),
    'ap-northeast-1': s3_endpoint('Asia Pacific(Tokyo)',
                                  's3-website-ap-northeast-1.amazonaws.com', 'Z2M4EHUR26P7ZW'),
    'ca-central-1': s3_endpoint('Canada(Central)',
                                's3-website.ca-central-1.amazonaws.com', 'Z1QDHH18159H29'),
    'cn-northwest-1': s3_endpoint('China(Ningxia)',
                                  's3-website.cn-northwest-1.amazonaws.com.cn', 'Not supported'),
    'eu-central-1': s3_endpoint('EU(Frankfurt)',
                                's3-website.eu-central-1.amazonaws.com', 'Z21DNDUVLTQW6Q'),
    'eu-west-1': s3_endpoint('EU(Ireland)',
                             's3-website-eu-west-1.amazonaws.com', 'Z1BKCTXD74EZPE'),
    'eu-west-2': s3_endpoint('EU(London)',
                             's3-website.eu-west-2.amazonaws.com', 'Z3GKZC51ZF0DB4'),
    'eu-west-3': s3_endpoint('EU(Paris)',
                             's3-website.eu-west-3.amazonaws.com', 'Z3R1K369G5AVDG'),
    'eu-north-1': s3_endpoint('EU(Stockholm)',
                              's3-website.eu-north-1.amazonaws.com', 'Z3BAZG2TWCNX0D'),
    'sa-east-1': s3_endpoint('South America(São Paulo)',
                             's3-website-sa-east-1.amazonaws.com', 'Z7KQH4QJS55SO'),
    'me-south-1': s3_endpoint('Middle East(Bahrain)',
                              's3-website.me-south-1.amazonaws.com', 'Z1MPMWCPA7YB62')
}

protected_buckets = []
protected_buckets.append("dmillikan-synology")
protected_buckets.append("dmillikan-mail")

def known_region(region):
    """Returns True if Region is Valid"""
    return region in region_endpoint


def get_region(region):
    """Returns Region Item"""
    return region_endpoint[region]


