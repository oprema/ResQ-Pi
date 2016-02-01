import RPi.GPIO as GPIO
import time
import multiprocessing
 
## Basic thread wrapper class for delta-timed LED pulsing
#
class ResqGpio:
  def __init__(self):
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(23, GPIO.OUT)
    GPIO.setup(24, GPIO.OUT)
    GPIO.setup(25, GPIO.OUT)

  # LED 1, 2, 3 on port 23, 24, 25, 0 all LEDs
  def led(self, number, state=True):
#    print 'LED ', number, state
    if number == 0:
      GPIO.output(23, state)
      GPIO.output(24, state)
      GPIO.output(25, state)
    elif number < 4:
      GPIO.output(number + 22, state)
    else:
      return False
    return True

  # a private method 
  def __led_worker(self, number):
#    print 'Starting worker'
    while True:
      self.led(number, True)
      time.sleep(0.5)
      self.led(number, False)
      time.sleep(0.5)
#    print 'Finished worker'

  # 
  def led_blink(self, number):
    p = multiprocessing.Process(target=self.__led_worker, args=(number,))
#    print 'BEFORE:', p, p.is_alive()
    p.start()
#    print 'DURING:', p, p.is_alive()
#    p.join()
#    print 'JOINED:', p, p.is_alive()
    return p

if __name__ == "__main__":
  gpio = AlarmGpio()
  gpio.led(0, False) # all off
  time.sleep(1)
  gpio.led(1, True) # LED 1 on
  time.sleep(1)
  gpio.led(2, True) # LED 2 on
  time.sleep(1)
  gpio.led(3, True) # LED 3 on
  gpio.led(0, False) # all off
  p = gpio.led_blink(0) # blink all LEDs (one sec period)
  time.sleep(10.5) # wait 10 seconds and terminate
  p.terminate()
