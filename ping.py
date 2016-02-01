import os
import setproctitle
import time
from multiprocessing import Process, Event

class GooglePing(object):
  def __init__(self, log, gpio = None):
    self._log = log
    self._gpio = gpio
    self._process = None
    self.exit = Event()

  def __ping(self, title):
    hostname = "www.google.com"
    was_down = False

    setproctitle.setproctitle(title)
    while not self.exit.is_set():
      # ping hostname ...
      response = os.system("ping -c 1 -w2 " + hostname + " > /dev/null 2>&1")
      # then check the response
      if response != 0:
        self._log.error(hostname + ' is unreachable!')
        was_down = False
      elif was_down:
        self._log.error(hostname + ' is up again!')

      if self._gpio != None:
        self._gpio.led(1, True) # LED 1 on
        time.sleep(0.2)
        self._gpio.led(1, False)  # LED 1 off
      time.sleep(15)

  def execute(self, title):
    self._process = Process(target = self.__ping, args = (title,))
    self._process.start()
    self._log.info("Pinging www.google.com.")
    return self._process


  def stop(self):
    if self._process is not None:
      self._log.info("Terminate ping.")
      self.exit.set()

if __name__ == "__main__":
  from logger import Logger
  log = Logger.get(verbose=False)
  gp = GooglePing(log)
  print gp.execute("ping ping ping")
  print "Execute Ping every 15 sec for a period of 45 sec ..."
  time.sleep(45)
  print "Exiting!"
  gp.stop()
  exit(0)
