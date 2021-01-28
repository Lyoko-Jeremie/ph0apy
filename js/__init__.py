# %%
# this is a mock, be used to let intelli work, for dev and test
import typing
import time
import threading

msgs = [
  'COM3 0 state h:2.15;x:1.5;y:1.7;\r\n',
  'COM4 0 state h:2.15;x:1.5;y:1.7;\r\n',
  'COM5 0 state h:2.15;x:1.5;y:1.7;\r\n',
  'COM6 0 state h:2.15;x:1.5;y:1.7;\r\n',
  'COM7 0 state h:2.15;x:1.5;y:1.7;\r\n',
  'COM3 0 state h:2.15;x:1.5;y:1.7;\r\n',
  'COM4 0 state h:2.15;x:1.5;y:1.7;\r\n',
  'COM5 0 state h:2.15;x:1.5;y:1.7;\r\n',
  'COM6 0 state h:2.15;x:1.5;y:1.7;\r\n',
  'COM7 0 state h:2.15;x:1.5;y:1.7;\r\n',
]

rr = []


def loadImports(list: typing.List[str]):
  pass


def printString(text: str):
  print(text)
  pass


def _setTimeoutImpl(addString: str, o):
  global rr
  rr.append(addString)
  pass


def _setTimeout(addString: str):
  threading.Timer(1.0, _setTimeoutImpl, (addString, '')).start()
  pass


# sendCmd(msgs[0])
# sendCmd('127.0.1.5 6 up 3')
# sendCmd('127.0.1.7 8 land')
def sendCmd(text: str):
  global rr
  ss = text.split()
  if len(ss) < 3:
    return False
  name = ss[0]
  id = int(ss[1])
  cmd = ' '.join(ss[2:])
  # print(name)
  # print(id)
  # print(cmd)
  _setTimeout(' '.join([name, str(id + 1), 'ok', '\r\n']))
  pass


def getBufMsgList() -> typing.List[str]:
  global rr
  l = msgs.copy()
  if len(rr) > 0:
    l.extend(rr)
    rr = []
    l.extend(msgs.copy())
  return l
  pass


def jsSleep(timeMs):
  startTime = time.time() * 1000
  endTime = time.time() * 1000
  while endTime - startTime < timeMs:
    endTime = time.time() * 1000
  pass


def jsSleepWithCallback(timeMs, cb):
  startTime = time.time() * 1000
  endTime = time.time() * 1000
  while endTime - startTime < timeMs:
    cb()
    endTime = time.time() * 1000
  pass


def jsSleepWithCallbackEvery(timeMs, everyTimeMs, cb):
  startTime = time.time() * 1000
  endTime = time.time() * 1000
  last = 0
  while endTime - startTime < timeMs:
    if (endTime - startTime) > (last * everyTimeMs):
      cb()
      last = last + 1
    endTime = time.time() * 1000
  pass


def _test():
  xxxx = getBufMsgList()
  sssss = ''.join(filter(lambda x: 'state' not in x, xxxx))
  print(sssss)


def _test2():
  jsSleep(1000)
  jsSleepWithCallback(1000, lambda: print('1'))
  jsSleepWithCallbackEvery(5000, 1000, lambda: print('1'))
  print('sssss')
