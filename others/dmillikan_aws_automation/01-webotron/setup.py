# -*- code utf-8 -*-

from setuptools import setup

setup(
    name='webotron',
    version='0.1',
    author='Daniel Millikan',
    author_email='dmillikan@gmail.com',
    description='allows creation and synchronization of local static website to s3 with cloudfront',
    license='GPLv3+',
    packages=['webotron'],
    url='https://github.com/dmillikan/aws_automation/tree/master/01-webotron/webotron',
    install_requires=[
        'click',
        'boto3'
    ],
    entry_points="""
        [console_scripts]
        webotron=webotron.webotron:cli
    """
)
