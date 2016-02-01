# Import the email modules we'll need
#import subprocess
import smtplib
#import socket
#import os
from email.mime.text import MIMEText

class SendEmail(object):
  def __init__(self, user, password, smtp_server, smtp_port=None):
    self.user = user
    self.password = password
    self.smtp_server = smtp_server
    self.smtp_port = smtp_port

  def deliver(self, from_, to, subject, msg):
    if self.smtp_port == None:
      smtpserver = smtplib.SMTP(self.smtp_server)
    else:
      smtpserver = smtplib.SMTP(self.smtp_server, self.smtp_port)
    smtpserver.set_debuglevel(0)
    smtpserver.ehlo()
    smtpserver.starttls()
    smtpserver.ehlo()
    smtpserver.login(self.user, self.password)
    msg = MIMEText(msg)
    msg['Subject'] = subject
    msg['From'] = from_
    msg['To'] = to
    smtpserver.sendmail(self.user, [to], msg.as_string())
    smtpserver.quit()
    
if __name__ == "__main__":
  email = SendEmail('jens@carroll.de', 'peaj511', 'mail.carroll.de', 25)
  email.deliver('alarm-pi@carroll.de', 'caro33@gmx.net', 'Hello this is Alarm-Pi',
    'Text to deliver')
