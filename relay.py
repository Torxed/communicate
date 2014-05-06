import select, json
from socket import *
from threading import *
from time import sleep

sockets = select.epoll()

class relay():
	def __init__(self):
		super(relay, self).__init__()
		self.sock = socket()
		self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		self.sock.bind(('10.8.0.1', 7113))
		self.sockets = {}
		sockets.register(self.sock.fileno(), select.EPOLLIN)

		self.output = []
		self.exit = False
		self.messages = {}

	def _send(self, what):
		self.output.append(what)

	def flush(self):
		## == Send all buffered outgoing messages
		for i in range(0, len(self.output)):
			msg = self.output.pop(0)
			if not type(msg) == bytes:
				msg = bytes(msg, 'UTF-8')

			sent = False
			for fd in self.sockets:
				try:
					self.sockets[fd].send(msg)
					sent = True
				except OSError:
					pass

			if not sent:
				self.output.append(msg)

		## == Recieve all incomming relay messages
		for fd, event in sockets.poll(0.2):
			if fd == self.sock.fileno() and event == select.EPOLLIN:
				ns, na = self.sock.accept()
				self.sockets[ns.fileno()] = ns
				sockets.register(ns.fileno(), select.EPOLLIN)
			else:
				tmp = self.sockets[fd].recv(8192)
				if len(tmp) == 0:
					# TODO: Remove socket
					continue
				try:
					data = json.loads(tmp.decode('utf-8'))
				except:
					# TODO: Remove socket
					continue

				if 'to' in data:
					if not data['to'] in self.messages:
						self.messages[data['to']] = []
					self.messages[data['to']].append(data['msg'])
				print('Relay-recieved:',tmp)

#	def run(self):
#		while not self.exit:
#			self.flush()
#			sleep(0.1)
#		sockets.unregister(self.sock.fileno())
#		self.sock.close()