#!/usr/bin/env python

from distutils.core import setup

setup(name='pos',
      version='0.0.0',
      description='Protocol adapter for web services',
      packages=['pos'],
      install_requires=['Flask', 'requests'],
      )
