#!/usr/bin/env python

import asyncore
import json
import traceback
import smtpd

import click
import requests

from email.message import Message
from email.parser import Parser


def _write(msg, fg=None):
  if not fg:
    click.echo(msg)
  else:
    click.echo(click.style(msg, fg=fg))

@click.command()
@click.option('--webhook-url', help='URL for your webhook integration', required=True)
@click.option('--authorization-token', default=None,
  help='Authorization token.  No messages will be forwarded if they do not include this token.')
@click.option('--listen-address', default='localhost:5025',
  help='Address to listen on.')
def run_server(webhook_url, authorization_token, listen_address):
  class SlackMailServer(smtpd.SMTPServer):
    def _process(self, peer, mailfrom, rcpttos, data):
      msg = Parser().parsestr(data)
      if authorization_token and not authorization_token in data:
        _write('Rejecting message: missing authorization token', fg='yellow')
        return

      if msg.is_multipart():
        body = msg.get_payload(0).as_string()
      else:
        body = msg.get_payload()

      r = requests.post(webhook_url, data=json.dumps({
        'text' : body,
        'username': msg['from']
      }))
      try:
        r.raise_for_status()
      except Exception, e:
        _write('Slack reported an error:', fg='red')
        _write(e, fg='red')


    def process_message(self, peer, mailfrom, rcpttos, data):
      try:
        _write('Processing message... %s, %s, %s' % (peer, mailfrom, rcpttos))
        self._process(peer, mailfrom, rcpttos, data)
      except Exception, e:
        _write('Failed to process message from %s' % mailfrom)
        _write(traceback.format_exc())

  host, port = listen_address.split(':')
  port = int(port)
  smtp_server = SlackMailServer((host, port), None)
  _write('Starting SMTP server on %s' % listen_address, fg='green')

  try:
    asyncore.loop()
  except KeyboardInterrupt:
    pass

if __name__ == '__main__':
  run_server()
