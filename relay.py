import select, json
from socket import *
from threading import *
from time import sleep

sockets = select.epoll()

class relay(Thread):
	def __init__(self):
		super(relay, self).__init__()
		Thread.__init__(self)
		self.sock = None
		self.reconnect()
		self.output = []
		self.exit = False
		self.messages = {}
		self.start()

	def reconnect(self):
		if self.sock:
			try:
				sockets.unregister(self.sock.fileno())
			except:
				pass
			self.sock.close()
		self.sock = socket()
		try:
			self.sock.connect(('127.0.0.1', 1337))
			sockets.register(self.sock.fileno(), select.EPOLLIN)
		except ConnectionRefusedError:
			return None
		return True

	def _send(self, what):
		self.output.append(what)

	def flush(self):
		for i in range(0, len(self.output)):
			msg = self.output.pop(0)
			if not type(msg) == bytes:
				msg = bytes(msg, 'UTF-8')
			try:
				self.sock.send(msg)
			except OSError:
				if self.reconnect():
					try:
						self.sock.send(msg)
					except OSError:
						self.output.append(msg)
				else:
					self.output.append(msg)
		for fd, event in sockets.poll(0.2):
			if fd == self.sock.fileno() and event == select.EPOLLIN:
				tmp = self.sock.recv(8192)
				if len(tmp) == 0:
					continue
				try:
					data = json.loads(tmp.decode('utf-8'))
				except:
					continue
				if 'to' in data:
					if not data['to'] in self.messages:
						self.messages[data['to']] = []
					self.messages[data['to']].append(data['msg'])
				print('Relay-recieved:',tmp)

	def run(self):
		while not self.exit:
			self.flush()
			sleep(0.1)
		sockets.unregister(self.sock.fileno())
		self.sock.close()