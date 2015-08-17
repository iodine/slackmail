import smtplib
from email.mime.text import MIMEText

def main():
  msg = MIMEText('Test message from SlackEmail')
  msg['Subject'] = 'This is a test message.'
  msg['From'] = 'you@domain.com'
  msg['To'] = 'your-friend@domain.com'

  s = smtplib.SMTP('localhost', 5025)
  s.sendmail('you@domain.com', ['your-friend@domain.com'], msg.as_string())
  s.quit()

if __name__ == '__main__':
  main()
