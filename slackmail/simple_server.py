import click
import smtpd
import traceback

from email.parser import Parser
from smtp_util import forward_message, echo, run_server, error

class SimpleServer(smtpd.SMTPServer):
  '''A basic forwarding server for a specific webhook.'''
  def __init__(self, listen_address, webhook_url, authorization_token):
    smtpd.SMTPServer.__init__(self, listen_address, None)
    self.webhook_url = webhook_url
    self.authorization_token = authorization_token

  def process_message(self, peer, mailfrom, rcpttos, data):
    msg = Parser().parsestr(data)
    try:
      echo('Processing message... %s, %s, %s' % (peer, mailfrom, rcpttos))
      forward_message(mailfrom, rcpttos, msg, self.webhook_url,
          self.authorization_token)
    except Exception, e:
      error('Failed to process message from %s' % mailfrom)
      error(traceback.format_exc())

@click.command()
@click.option('--webhook-url', help='URL for your webhook integration', required=True)
@click.option('--authorization-token', default=None,
  help='Authorization token.  No messages will be forwarded if they do not include this token.')
@click.option('--listen-address', default='localhost:5025',
  help='Address to listen on.')
def simple_server(webhook_url, authorization_token, listen_address):
  host, port = listen_address.split(':')
  port = int(port)
  server = SimpleServer((host, port), webhook_url, authorization_token)
  run_server(server)

