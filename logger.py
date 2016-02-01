import logging
import logging.handlers
import sys, time

# Make a class we can use to capture stdout and sterr in the log
class MyLogger(object):
  def __init__(self, logger, level):
    """Needs a logger and a logger level."""
    self._logger = logger
    self._level = level

  def write(self, message):
    # Only log if there is a message (not just a new line)
    if message.rstrip() != "":
      self._logger.log(self._level, message.rstrip())

  def flush(self):
    pass

class Logger(object):
  @classmethod
  def get(cls, path=None, verbose=False):
    # create logger
    logger = logging.getLogger('__name__')
    if verbose:
      logger.setLevel(logging.DEBUG)
    else:
      logger.setLevel(logging.INFO)

    # create console handler and set level to debug
    if path is None:
      handler = logging.StreamHandler()
    else:
      # Make a handler that writes to a file, making a new file
      # at midnight and keeping 3 backups
      handler = logging.handlers.TimedRotatingFileHandler(path, when="midnight", backupCount=3)

    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s',
      '%Y-%m-%d %H:%M:%S')

    # add formatter to handler
    handler.setFormatter(formatter)

    # add handler to logger
    logger.addHandler(handler)

    # Replace stdout with logging to file at INFO level
    sys.stdout = MyLogger(logger, logging.INFO)
    # Replace stderr with logging to file at ERROR level
    sys.stderr = MyLogger(logger, logging.ERROR)

    return logger
 
if __name__ == "__main__":
  #logger = Logger.get("bla.log")
  logger = Logger.get(verbose=True)
  logger.debug('debug message')
  logger.info('info message')
  logger.warn('warn message')
  logger.error('error message')
  logger.critical('critical message')

  i=0
  # Loop forever, doing something useful hopefully:
  while True:
    logger.info("The counter is now " + str(i))
    print "This is a print"
    i += 1
    time.sleep(5)
    if i == 3:
      j = 1/0  # cause an exception to be thrown and the program to exit
