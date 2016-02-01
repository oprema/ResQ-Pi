import pylirc
import signal
import time

class ResqException(Exception):
  pass

class ResqLirc(object):
  def __init__(self, log, gpio):
    self.blocking = 1
    self.enter_pressed = 0
    self.log = log
    self.gpio = gpio
    self.lirc_init = pylirc.init("pylirc", "/home/pi/.lircrc", self.blocking)

  def __alarmHandler(self, signum, frame):
    raise ResqException

  def __nextcode(self, log):
    s = []
    if (self.lirc_init):
      # Read next code
      s = pylirc.nextcode(1)
    else:
      log.warn("Pylirc: ughhh something went wrong!")
      time.sleep(5)
    return s

  def cleanup(self):
    # Clean up lirc
    pylirc.exit()

  def wait_alarm(self, mode = "3times"):
    # wait for next lirc command (we are blocking here)
    c = self.__nextcode(self.log)
    code = { "config" : "" }

    while(c):
      for (code) in c:
        repeat = int(code["repeat"])
        key = code["config"]
        #print "key: %s, repeat: %s" % (key, repeat)

        if (mode == "3times"):
          if (key == "enter" and repeat == 0):
            self.enter_pressed += 1
            self.gpio.led(self.enter_pressed, True) # LED on
            self.log.info("Pylirc: KEY_ENTER pressed %d time(s)", self.enter_pressed)
          elif (key == "right" and self.enter_pressed == 2):
            self.enter_pressed = 0
            self.log.info("Pylirc: KEY_RIGHT pressed, detecting Test-Alarm")
            return "test-alarm"

          if (self.enter_pressed >= 3):
            self.enter_pressed = 0
            return "alarm"

        elif (mode == "long"):
          if (key == "enter" and repeat >= 50):
            self.log.info("Pylirc: KEY_ENTER pressed for a long time")
            return "alarm"
        else:
          return "no-alarm"

        signal.signal(signal.SIGALRM, self.__alarmHandler)
        signal.alarm(20) # timeout 20 secs
        try:
          c = self.__nextcode(self.log)
          signal.alarm(0) # no timeout
        except ResqException:
          signal.signal(signal.SIGALRM, signal.SIG_IGN)
          self.log.info("Pylirc: Nextcode timeout")
          self.enter_pressed = 0
          return 'timeout'

    return "no alarm - and no surprises" # no alarm

if __name__ == "__main__":
  from logger import Logger
  from gpio import ResqGpio

  gpio = ResqGpio()
  gpio.led(0, False) # all LEDs off
  log = Logger.get(verbose=True)
  lirc = ResqLirc(log, gpio)
  print "Press 3 times KEY_ENTER (timeout 20 sec)"
  print lirc.wait_alarm()
  time.sleep(2)
  gpio.led(0, False) # all LEDs off
  print "Press 3 times KEY_ENTER (timeout 20 sec)"
  print lirc.wait_alarm()
  time.sleep(2)
  gpio.led(0, False) # all LEDs off
  print "Press one time KEY_ENTER for at least 5 secs"
  print lirc.wait_alarm("long")
  lirc.cleanup()
