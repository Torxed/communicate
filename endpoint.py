import json
from socket import *
from threading import *
from time import sleep

class relay(Thread):
	def __init__(self, socket):
		super(relay, self).__init__()
		Thread.__init__(self)
		self.sock = socket
		self.exit = False
		self.start()

	def flush(self):
		for i in range(0, len(self.output)):
			msg = self.output.pop(0)
			if not type(msg) == bytes:
				msg = bytes(msg, 'UTF-8')
			try:
				self.send(msg)
			except OSError:
				if self.reconnect():
					try:
						self.send(msg)
					except OSError:
						self.output.append(msg)
				else:
					self.output.append(msg)

	def run(self):
		while not self.exit:
			try:
				data = json.loads(self.sock.recv(8192).decode('utf-8'))
			except ValueError:
				break
			if 'source' in data:
				print('[/'+data['source']+'/'+data['channel']+']', data['from'] + ': ' + data['msg'])
		self.sock.close()

sock = socket()
sock.bind(('', 1337))
sock.listen(4)
while 1:
	ns, na = sock.accept()
	relay(ns)