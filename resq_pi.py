#!/usr/bin/python
# Copyright: 2015 Jens Carroll, Inventronik GmbH
# These sources are released under the terms of the MIT license: see LICENSE
"""
Description:
ResQ-Pi - A Raspberry Pi Rescue System

Usage: resq_pi.py [-acprhv]

You must have root privileges to start resq_pi.py

Options:
  -a, --alarm           Send a test alarm.
  -c, --credits         Get SMS credits.
  -p, --resetpass       Reset password (default: admin).
  -r, --resetdb         Reset sqlite database.
  -h, --help            This screen.
  -v, --verbose         Verbose.
"""
import multiprocessing, setproctitle, signal, sys, os, re, docopt # Docopt is a library for parsing command line arguments
from logger import Logger
from time import sleep
from fileutil import FileUtil
from sqlite import ResqStore
from gpio import ResqGpio
from ping import GooglePing
from send_email import SendEmail
from resq_lirc import ResqLirc
from gammu_sms import GammuSms

def start_ping():
  # Start Google ping process
  if db.use_email():
    log.info("Start ping process.")
    ping.execute("resq-pi [ping]")
  else:
    log.info("E-Mail notification is off. Do not start ping process.")

def get_sms_credits():
  if db.use_sms():
    log.info("Try to get prepaid credits.")
    credit = GammuSms.get_credits(log)
    log.info("Prepaid credit is EUR %s." % credit)
    if credit != '--':
      db.save_credit(credit)

def resqpi_endless_loop(test):
  # Change title
  setproctitle.setproctitle("resq-pi [master]")

  # Start Google ping if E-Mail is enabled
  start_ping()

  while True:
    if not test:
      log.info("Waiting for Lirc commands.")
      result = lirc.wait_alarm() # in blocling mode
    else:
      result = "test-alarm"
      test = False

    if result == "alarm":
      exec_alarm(db, False)
    elif (result == "test-alarm"):
      exec_alarm(db, True)
    else:
      log.debug("Lirc: " + result)
      if result == 'timeout':
        gpio.led(0, False) # a timeout occurred

def signal_handler(signal, frame):
  log.debug("ResQ-Pi stops. Pid was %s" % os.getpid())
  lirc.cleanup()
  ping.stop()
  sleep(2)
  sys.exit(0)

def email_alarm(participants, test):
  plist = []
  for p in participants:
    if p['email_address'] != '':
       plist.append(p['email_address'])
  if plist:
    logstr = "Send email to: %s" % ", ".join(plist)
    log.info(logstr)
    # Now send all email notifications
    send_email = SendEmail(*db.email_settings())
    for email_addr in plist:
      send_email.deliver('jens@carroll.de', email_addr, *db.email_notification(test))

def sms_alarm(participants, test):
  global gammu

  plist = []
  for p in participants:
    if p['phone_number'] != '':
       plist.append(p['phone_number'])
  if plist:
    # Start Gammu when we need it!
    if gammu == None:
      gammu = GammuSms(log)

    logstr = "Send SMS to: %s" % ", ".join(plist)
    log.info(logstr)
    for phone_number in plist:
      gammu.send_sms(phone_number, db.sms_notification(test))

def exec_alarm(db, test = False):
  log.info("Execute %s" % "Test-Alarm" if test else "Alarm")
  participants = db.list_participants(test)
  p = None
  gpio.led(0, False)
  if len(participants) > 0:
    p = gpio.led_blink(0)
  if db.use_email():
    email_alarm(participants, test)
  if db.use_sms():
    sms_alarm(participants, test)
  db.add_log(test, "Send %d notification(s)" % len(participants))
  if p != None:
    sleep(5)
    p.terminate()
    gpio.led(0, False)

def main():
  global log, gpio, lirc, ping, db, gammu

  # Parse arguments, use file docstring as a parameter definition
  args = docopt.docopt(__doc__, version='0.1a')
  #print args

  # Create directory if it doesn't exist
  futil = FileUtil("/home/pi/.resq-pi")
  gammu = None

  # Create a logger
  if args["--verbose"]:
    log = Logger.get(verbose = True)
  else:
    log = Logger.get(futil.path + "/resq-pi.log", False)
  log.info("*** Start ResQ-Pi ***")

  # Be sure we have root privileges
  if os.geteuid() != 0:
    exit("You need to have root privileges. Exiting.")
    
  # Ctrl-C and SIGTERM handler
  signal.signal(signal.SIGINT, signal_handler)
  signal.signal(signal.SIGTERM, signal_handler)

  # Get access to the resq-pi database
  db = ResqStore(futil.path + "/resq-pi.db")
  if not db.exist():
    log.info("No database found. Will create one.")
    db.create_tables() # if not already created
    db.reset_tables()  # and initialize

  # Initalize GPIO, Lirc, GooglePing ...
  gpio = ResqGpio()
  gpio.led(0, False) # all LEDs off
  lirc = ResqLirc(log, gpio)
  ping = GooglePing(log, gpio)

  test = False
  if args["--alarm"]:
    test = True

  if args["--resetdb"]:
    log.info("Reset database")
    db.reset_tables()
  elif args["--resetpass"]:
    log.info("Reset password")
    db.reset_password()
  elif args["--credits"]:
    get_sms_credits()
  else:
    resqpi_endless_loop(test)

if __name__ == '__main__':
  main()
