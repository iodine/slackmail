#!/usr/bin/env python

import asyncore
import json

import click
import requests

from email.message import Message

def echo(msg, fg=None):
  if not fg:
    click.echo(msg)
  else:
    click.echo(click.style(msg, fg=fg))

def warn(msg):
  return echo(msg, fg='yellow')

def error(msg):
  return echo(msg, fg='red')


def _msg_text(msg):
  if msg.is_multipart():
    return msg.get_payload(0).as_string()
  else:
    return msg.get_payload()

Message.text = _msg_text

class SMTPError(Exception):
  def __init__(self, code, msg):
    self.code = code
    self.message = msg

  def __repr__(self):
    return '%d %s' % (self.code, self.message)


def forward_message(mailfrom, rcpttos, msg, webhook_url, authorization_token=None):
  if authorization_token and not authorization_token in msg.as_string():
    raise SMTPError(554, 'Rejecting message: missing or invalid authorization token')

  try:
    r = requests.post(webhook_url, data=json.dumps({
      'text' : msg.text(),
      'username': msg['from']
    }))
    r.raise_for_status()
  except Exception, e:
    error('Slack reported an error: %s' % e)
    raise SMTPError(554, 'Error posting to webhook')


def run_server(server):
  echo('Starting SMTP server on %s' % (server._localaddr,), fg='green')
  try:
    asyncore.loop()
  except KeyboardInterrupt:
    pass
