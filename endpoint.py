import json
from socket import *
from threading import *
from time import sleep

class relay(Thread):
	def __init__(self, handles):
		super(relay, self).__init__()
		Thread.__init__(self)
		self.sock = socket()
		self.sock.connect(('10.8.0.1', 7113))
		self.handles = handles
		self.exit = False
		self.start()

#	def reconnect(self):
#		if self.sock:
#			try:
#				sockets.unregister(self.sock.fileno())
#			except:
#				pass
#			self.sock.close()
#		self.sock = socket()
#		try:
#			self.sock.connect(('10.8.0.1', 7113))
#			sockets.register(self.sock.fileno(), select.EPOLLIN)
#		except ConnectionRefusedError:
#			return None
#		return True

#	def flush(self):
#		for i in range(0, len(self.output)):
#			msg = self.output.pop(0)
#			if not type(msg) == bytes:
#				msg = bytes(msg, 'UTF-8')
#			try:
#				self.send(msg)
#			except OSError:
#				if self.reconnect():
#					try:
#						self.send(msg)
#					except OSError:
#						self.output.append(msg)
#				else:
#					self.output.append(msg)

	def _send(self, what):
		what = bytes(json.dumps(what), 'UTF-8')
		self.sock.send(what)

	def run(self):
		while not self.exit:
			try:
				data = json.loads(self.sock.recv(8192).decode('utf-8'))
			except ValueError:
				break
			if 'source' in data:
				self.handles['/'+data['source']+'/'+data['channel']] = self._send
				if 'flag' in data and data['flag'] == 'notice':
					print('(/'+data['source']+'/'+data['channel']+')', data['from'] + ': ' + data['msg'])
				else:
					print('[/'+data['source']+'/'+data['channel']+']', data['from'] + ': ' + data['msg'])
		self.sock.close()

class handler(Thread):
	def __init__(self, handles):
		Thread.__init__(self)
		self.handles = handles
		self.states = {}
		self.start()

	def run(self):
		while 1:
			cmd = input('')
			if cmd[0] == '/':
				if ' ' in cmd:
					path, msg = cmd.split(' ',1)
					if path in self.handles:
						self.handles[path]({'to' : path, 'msg' : msg})
						self.states['lastpath'] = path
			elif cmd[0] == '!':
				pass
			else:
				if 'lastpath' in self.states and self.states['lastpath'] != '':
					self.handles[self.states['lastpath']]({'to' : self.states['lastpath'], 'msg' : cmd})

handles = {}
handler(handles)
relay(handles)