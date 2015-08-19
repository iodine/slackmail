import click
import smtpd
import sqlalchemy
import sys
import traceback

from email.parser import Parser

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String

from smtp_util import forward_message, echo, run_server, error, SMTPError

Base = declarative_base()

class Hook(Base):
  __tablename__ = 'hooks'
  url = Column(String, primary_key=True)
  email = Column(String, unique=True)
  auth_token = Column(String)

  def __repr__(self):
    return '<Hook %s (%s)>' % (self.hook_url, self.email)

def _create_schema(engine):
  Base.metadata.create_all(engine)

def _contains(lst, test_fn):
  for item in lst:
    if test_fn(item):
      return True

  return False


class DBServer(smtpd.SMTPServer):
  '''
  A server that supports adding and removing hooks dynamically.

  Hooks are stored using the passed in SQLAlchemy model.
  '''
  def __init__(self, listen_address, engine):
    smtpd.SMTPServer.__init__(self, listen_address, None)
    self._engine = engine

  def _session(self):
    from sqlalchemy.orm import sessionmaker
    return sessionmaker(bind=self._engine)()

  def _parse_message(self, msg):
    'Parse colon delimited lines from a mail message.'
    result = {}

    text = msg.text()
    lines = [l.strip() for l in text.split('\n')]
    for line in lines:
      if not ':' in line:
        continue
      key, value = line.split(':', 1)
      key = key.lower().strip()
      value = value.strip()
      result[key] = value
    return result

  def _add_hook(self, mailfrom, mailto, msg):
    config = self._parse_message(msg)
    try:
      email = config['target_email']
      webhook_url = config['webhook_url']
      auth_token = config.get('auth', None)

      hook = Hook(url=webhook_url, auth_token=auth_token, email=email)
      session = self._session()
      session.add(hook)
      session.commit()
    except KeyError, e:
      raise SMTPError(510, 'Missing required field: %s' % e.message)

  def _remove_hook(self, mailfrom, mailto, msg):
    config = self._parse_message(msg)
    try:
      email = config['target_email']
      webhook_url = config['webhook_url']
      auth_token = config.get('auth', None)

      session = self._session()
      match = session.query(Hook).filter(
        Hook.url == webhook_url,
        Hook.email == email,
        Hook.auth_token == auth_token
      ).one()
      session.delete(match)
      session.commit()
    except KeyError, e:
      raise SMTPError(510, 'Missing required field: %s' % e.message)

  def _forward(self, mailfrom, rcpttos, msg):
    session = self._session()
    hook = session.query(Hook).filter(Hook.email == rcpttos[0]).one()
    forward_message(mailfrom, rcpttos, msg, hook.url, hook.auth_token)

  def process_message(self, peer, mailfrom, rcpttos, data):
    try:
      echo('Processing message... %s, %s, %s' % (peer, mailfrom, rcpttos))

      add_request = _contains(rcpttos, lambda address: 'add-hook@' in address)
      remove_request = _contains(rcpttos, lambda address: 'remove-hook@' in address)
      msg = Parser().parsestr(data)
      if add_request:
        self._add_hook(mailfrom, rcpttos, msg)
      elif remove_request:
        self._remove_hook(mailfrom, rcpttos, msg)
      else:
        self._forward(mailfrom, rcpttos, msg)
    except SMTPError as e:
      error('Failed to process message from %s.\n%s' % (mailfrom, e))
      return repr(e)
    except sqlalchemy.exc.IntegrityError as e:
      error('Ignoring request to add an existing webhook')
      return '554 Hook already exists.'
    except:
      e = sys.exc_info()[0]
      error('Failed to process message from %s' % mailfrom)
      error(traceback.format_exc())
      return '554 Error while processing message. %s' % e

@click.command()
@click.option('--listen-address', default='localhost:5025',
  help='Address to listen on.')
def db_server(listen_address):
  host, port = listen_address.split(':')
  port = int(port)

  from sqlalchemy import create_engine
  engine = create_engine('sqlite:///email.db')
  _create_schema(engine)

  run_server(DBServer((host, port), engine))

if __name__ == '__main__':
  db_server()
