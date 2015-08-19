import smtplib
from email.mime.text import MIMEText

def _send(data, from_email, to_email):
  msg = MIMEText(data)
  msg['Subject'] = 'This is a test message.'
  s = smtplib.SMTP('localhost', 5025)
  s.sendmail(from_email, [to_email], msg.as_string())
  s.quit()

def test_forward():
  _send('Woop woop woop woop woop...', 'you@domain.com', 'my-test-hook@rjp.io')

def test_add_hook():
  _send('''
  target_email: my-test-hook@rjp.io
  webhook_url: https://awdawldiawd.slack.com/webhook?token=123
  auth_token: elderberries
  ''', 'you@domain.com', 'add-hook@slackmail.com')

def test_remove_hook():
  _send('''
  target_email: my-test-hook@rjp.io
  webhook_url: https://awdawldiawd.slack.com/webhook?token=123
  auth_token: elderberries
  ''', 'you@domain.com', 'remove-hook@slackmail.com')

def main():
  try:
    test_remove_hook()
  except:
    pass

  # test that we can add and remove hooks properly
  test_add_hook()
  test_remove_hook()
  test_add_hook()
  test_remove_hook()
  test_add_hook()
  test_remove_hook()

  # try to forward our message.
  test_add_hook()
  test_forward()

if __name__ == '__main__':
  main()
