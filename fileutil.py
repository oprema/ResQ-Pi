import os, errno

class FileUtil(object):
  def __init__(self, path):
    self.path = os.path.join(os.getcwd(), path)
    try:
      os.makedirs(self.path, 0750)
    except OSError as exc:
      if exc.errno == errno.EEXIST and os.path.isdir(self.path):
        pass
      else:
        raise

  def path(self):
    return self.path

if __name__ == "__main__":
  fu = FileUtil(".progdir")
  print "Path is: %s" % fu.path
  