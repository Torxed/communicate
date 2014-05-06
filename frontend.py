import json
from socket import *
from threading import *
from time import sleep
import select

class relay():
	def __init__(self):
		super(relay, self).__init__()
		self.sock = socket()
		self.sock.connect(('10.8.0.1', 7113))
		self.socketwatch = select.epoll()
		self.socketwatch.register(self.sock.fileno(), select.EPOLLIN)
		self.exit = False

	def _send(self, what):
		what = bytes(json.dumps(what), 'UTF-8')
		self.sock.send(what)

	def flush(self):
		for fd, event in self.socketwatch.poll(0.2):
			if event == select.EPOLLIN:
				try:
					data = json.loads(self.sock.recv(8192).decode('utf-8'))
				except ValueError:
					break
				if 'source' in data:
					if 'flag' in data and data['flag'] == 'notice':
						print('(/'+data['source']+'/'+data['channel']+')', data['from'] + ': ' + data['msg'])
					else:
						print('[/'+data['source']+'/'+data['channel']+']', data['from'] + ': ' + data['msg'])

	def _close(self):
		self.socketwatch.unregister(self.sock.fileno())
		self.sock.close()

class handler():
	def __init__(self):
		self.relay = relay()
		self.states = {}

	def run(self):
		while 1:
			cmd = input('')
			if cmd[0] == '/':
				if ' ' in cmd:
					path, msg = cmd.split(' ',1)
					self.relay._send({'to' : path, 'msg' : msg})
					self.states['lastpath'] = path
			elif cmd[0] == '!':
				if cmd == '!quit':
					break
			else:
				if 'lastpath' in self.states and self.states['lastpath'] != '':
					self.relay._send({'to' : self.states['lastpath'], 'msg' : cmd})

if __name__ == '__main__':
	handler().run()