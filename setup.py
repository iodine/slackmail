#!/usr/bin/python

import setuptools

setuptools.setup(
  name='slackmail',
  version='0.01',
  url='http://github.com/iodine/slackmail',
  install_requires=[
    'click',
    'requests'
  ],
  description=('Email-to-slack bridge.'),
  packages=['slackmail'],
  zip_safe=False,
  test_suite = 'nose.collector',
  entry_points='''
  [console_scripts]
  slackmail=slackmail.main:run_server
  '''
)
