import subprocess
import re
import gammu
import gammu.smsd
import sys

class GammuSms(object):
  def __init__(self, log):
    # Create object for talking with phone
    self.state_machine = gammu.StateMachine()
    # Read the configuration (~/.gammurc)
    self.state_machine.ReadConfig(Filename='/home/pi/.gammurc')
    # Connect to the phone
    self.state_machine.Init()
    # Logger
    self.log = log
    # Setup for incoming calls
    self.incoming()

  def callback(sm, type, data):
      '''
      This callback receives notification about incoming event.

      @param sm: state machine which invoked action
      @type sm: gammu.StateMachine
      @param type: type of action, one of Call, SMS, CB, USSD
      @type type: string
      @param data: event data
      @type data: hash
      '''
      self.log.info('Received incoming event type %s, data:' % type)
      self.log.info(data)

  def send_sms(self, phone_number, text):
    # Prepare message data
    # We tell that we want to use first SMSC number stored in phone
    message = {
        'Text': text,
        'SMSC': {'Location': 1},
        'Number': phone_number,
    }
    # Actually send the message
    self.state_machine.SendSMS(message)

  def send_smsd(self, phone_number, text):
    # Send SMS via smsd. Insert message in smsd send queue.
    smsd = gammu.smsd.SMSD('/etc/gammu-smsdrc')
    message = {
        'Text': text,
        'SMSC': {'Location': 1},
        'Number': phone_number,
    }
    smsd.InjectSMS([message])

  def signal_quality(self):
    q = self.state_machine.GetSignalQuality()
    return '%d%%' % q['SignalPercent']

  def incoming(self):
    # Set callback handler for incoming notifications
    self.state_machine.SetIncomingCallback(self.callback)

    # Enable notifications from calls
    try:
      self.state_machine.SetIncomingCall()
    except gammu.ERR_NOTSUPPORTED:
      self.log.info('Incoming calls notification is not supported.')

    # Enable notifications from cell broadcast
    try:
      self.state_machine.SetIncomingCB()
    except gammu.ERR_NOTSUPPORTED:
      self.log.info('Incoming CB notification is not supported.')
    except gammu.ERR_SOURCENOTAVAILABLE:
      self.log.info('Cell broadcasts support not enabled in Gammu.')

    # Enable notifications from incoming SMS
    try:
      self.state_machine.SetIncomingSMS()
    except gammu.ERR_NOTSUPPORTED:
      self.log.info('Incoming SMS notification is not supported.')

    # Enable notifications for incoming USSD
    try:
      self.state_machine.SetIncomingUSSD()
    except gammu.ERR_NOTSUPPORTED:
      self.log.info('Incoming USSD notification is not supported.')
    self.log.info('Gammu incoming callback established')

  @staticmethod
  def get_credits(log):
    i = 0
    while i < 3:
      try:
        log.info("Execute Gammu subprocess ... this might take some time!")
        output = subprocess.check_output("gammu -c /home/pi/.gammurc getussd *100# 2>&1", shell=True)
        log.info("Finished Gammu subprocess.")
        credit_balance = re.findall("\d+.\d+", output)
        if len(credit_balance) <= 0:
          continue
        return credit_balance[0] if len(credit_balance) > 0 else "--"
      except subprocess.CalledProcessError:
        i = i + 1
        log.error("Error: GammuSms CalledProcessError %d" % i)
    return "--"

if __name__ == "__main__":
  from logger import Logger
  log = Logger.get(verbose=False)

  sms = GammuSms(log)
  sms.send_sms('', 'python-gammu testing message')
  print GammuSms.get_credits(log)
