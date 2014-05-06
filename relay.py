from socket import *
from threading import *
from time import sleep

class relay(Thread):
	def __init__(self):
		super(relay, self).__init__()
		Thread.__init__(self)
		self.sock = None
		self.reconnect()
		self.output = []
		self.exit = False
		self.start()

	def reconnect(self):
		if self.sock:
			self.sock.close()
		self.sock = socket()
		try:
			self.sock.connect(('127.0.0.1', 1337))
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

	def run(self):
		while not self.exit:
			self.flush()
			sleep(0.1)
		self.sock.close()