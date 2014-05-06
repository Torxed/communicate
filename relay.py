import select, json
from socket import *
from time import sleep


class relay():
	def __init__(self):
		self.sock = socket()
		self.sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		print('Relay binding to: 10.8.0.1:7113')
		self.sock.bind(('10.8.0.1', 7113))
		self.sock.listen(4)
		self.sockets = {}
		self.socketwatch = select.epoll()
		self.socketwatch.register(self.sock.fileno(), select.EPOLLIN)

		self.output = []
		self.dummy = None
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
		for fd, event in self.socketwatch.poll(0.2):
			if fd == self.sock.fileno() and event != 16:
				ns, na = self.sock.accept()
				self.sockets[ns.fileno()] = ns
				self.socketwatch.register(ns.fileno(), select.EPOLLIN)
			elif event == select.EPOLLIN:
				try:
					tmp = self.sockets[fd].recv(8192)
				except OSError:
					# TODO: Remove socket
					continue
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