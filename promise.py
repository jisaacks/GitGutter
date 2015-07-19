from threading import Lock

class Promise:
  def __init__(self):
    self.value = None
    self.mutex = Lock()
    self.callbacks = []

  def updateValue(self, new_value):
    if (self.mutex.acquire(blocking = False) and self.value is None):
      self.value = new_value
      for cb in self.callbacks:
        cb(new_value)
      self.mutex.release()
    else:
      raise RuntimeError("cannot set the value of an already resolved promise")

  def addCallback(self, cb):
    self.mutex.acquire(blocking = True)
    self.callbacks.append(cb)
    self.mutex.release()
    return self

  def map(self, f):
    fp = Promise()
    def chain(v):
      fp.updateValue(f(v))
    self.addCallback(chain)
    return fp

  def flatMap(self, f):
    fp = Promise()
    def chain(v):
      f(v).addCallback(fp.updateValue)
    self.addCallback(chain)
    return fp

class ConstPromise:
  def __init__(self, value):
    self.value = value

  def updateValue(self, new_value):
    raise RuntimeError("cannot set the value of an ConstPromise")

  def addCallback(self, cb):
    cb(self.value)
    return self

  def map(self, f):
    return ConstPromise(f(self.value))

  def flatMap(self, f):
    return f(self.value)