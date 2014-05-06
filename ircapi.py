#!C:/python33/python

import asyncore, socket, traceback, sys, json
from threading import *
from socket import *
from time import sleep, strftime, localtime, time
from os import _exit

#__password__ = ''
ircparsers = __import__('ircparser')
relay = __import__('relay').relay()

class chatRoom(Thread):
	def __init__(self, room, identity, send):
		Thread.__init__(self)
		self.identity = identity
		self.send = send
		self.room = room
		self.people = {}
		self.muted = False
		self.graceperiod = None
		self.start()

	def sad(self, who, what):
		if self.room == self.identity or what[:len(self.identity)] == self.identity or (self.graceperiod and time() - self.graceperiod < 60*5):
			if what[:len(self.identity)] == self.identity: what = what[len(self.identity):].strip(' :')
			print('[relay::/irc/' + self.room + '] ' + who + ': ' + what)
			relay._send(json.dumps({'from' : who, 'msg' : what, 'channel' : self.room, 'source' : 'irc'}))
			self.graceperiod = time()
		elif self.identity in what:
			print('[relay::notice::/irc/' + self.room + '] ' + who + ': ' + what)
			relay._send(json.dumps({'from' : who, 'msg' : what, 'channel' : self.room, 'source' : 'irc', 'flag' : 'notice'}))
		else:
			print('[' + self.room + '] ' + who + ': ' + what)

	def write(self, what):
		print('[' + self.room + '] ' + self.identity + ': ' + what)
		self.send('PRIVMSG ' + self.room + ' :' + what)

	def mode(self, who, mode):
		self.people[who] = mode
	def join(self, who, mode):
		print(who,'joined',self.room)
		self.mode(who, mode)
	def part(self, who):
		print(who,'left',self.room)
		if who in self.people:
			del(self.people[who])
	def listPeople(self):
		for person in self.people:
			yield person

	def run(self):
		while 1:
			if '/irc/'+self.room in relay.messages and len(relay.messages['/irc/'+self.room]) > 0:
				msg = relay.messages['/irc/'+self.room].pop(0)
				self.write(msg)
				self.graceperiod = time()
			sleep(1)

class irc(Thread, asyncore.dispatcher):
	def __init__(self, config=None):
		self.conf = config
		if not self.conf:
			self.conf = {}
		if not 'server' in self.conf:
			self.conf['server'] = 'dreamhack.se.quakenet.org'
		if not 'port' in self.conf:
			self.conf['port'] = 6667
		if not 'nickname' in self.conf:
			self.conf['nickname'] = 'DoXiD'
		if not 'userid' in self.conf:
			self.conf['userid'] = 'DoXiD'
		if not 'fullname' in self.conf:
			self.conf['fullname'] = 'Kaylee Frye'
		if not 'channels' in self.conf:
			self.conf['channels'] = [('#dreamhack.crew', 'password'), '#DHSupport']
		if not 'password' in self.conf:
			try:
				self.conf['password'] = __password__
			except:
				self.conf['password'] = input('Enter your IRC password: ')
				if len(self.conf['password']) == 0:
					self.conf['password'] = False

		self.channels = {}
		self.channels[self.conf['nickname']] = chatRoom(self.conf['nickname'], self.conf['nickname'], self._send)
		self.messages = {}

		self.inbuffer = []
		self.buffer = []
		self.lockedbuffer = False
		self.is_writable = False

		self.MOTD = None
		self.exit = False

		asyncore.dispatcher.__init__(self)
		Thread.__init__(self)

		self.create_socket(AF_INET, SOCK_STREAM)
		try:
			self.connect((self.conf['server'], self.conf['port']))
		except:
			print('Could not connect to ' + str(self.conf['server']), 'IRC')
			return None

		self.buffer.append('NICK ' + self.conf['nickname'] + '\r\n')
		self.buffer.append('USER ' + self.conf['userid'] + ' ' + self.conf['server'] + ' ' + self.conf['nickname'] + ' :' + self.conf['fullname'] + '\r\n')
		self.ircparse = ircparsers.ircparsers(self._send, self.conf, self.channels)

		#self.is_writable = True
		self.start()

	def refstr(self, what):
		while len(what) > 0 and what[-1] in ('\r', '\n', ':', ' ', '	'):
			what = what[:-1]
		while len(what) > 0 and what[0] in ('\r', '\n', ':', ' ', '	'):	
			what = what[1:]
		return what

	def compare(self, obj, otherobj):
		return (str(obj).lower() == str(otherobj).lower()[:len(str(obj))])
	def _in(self, obj, otherobj):
		return (str(obj).lower() in str(otherobj).lower())

	def parse(self):
		self.lockedbuffer = True

		row = ''
		while not '\r\n' in row:
			try:
				row += self.inbuffer.pop(0)
			except IndexError:
				self.inbuffer.append(row)
				return

		row = row.strip('\r\n')
		if len(row) == 0:
			self.lockedbuffer = False
			return

		if self.compare('PING', row):
			self._send('PONG ' + row[5:])
		elif self._in('no ident response', row):
			print('Sending NICK + User')
			self.is_writable = True
		elif not self.MOTD:
			if not 'motd' in self.conf:
				self.conf['motd'] = ''
			self.conf['motd'] += row
			if self._in('End of /MOTD command', row):
				if self.conf['password']:
					if 'quakenet.org' in self.conf['server']:
						print('!Authenticating with Q@CServe.quakenet.org')
						self._send('PRIVMSG Q@CServe.quakenet.org :AUTH '+self.conf['nickname'] + ' ' + self.conf['password'])
					else:
						pass #self._send('PRIVMSG NickServ :identify ' + self.conf['nickname'] + ' ' + self.conf['password'])

				for chan in self.conf['channels']:
					if len(chan) <= 0: continue
					if type(chan) == tuple:
						chan, password = chan
						self._send('JOIN ' + chan + ' ' + password)
					else:
						self._send('JOIN ' + chan)
					self.channels[chan] = chatRoom(chan, self.conf['nickname'], self._send)

				self.MOTD = True

		elif self.MOTD:
			#print('Prasing row:',row)

			functions = {
				' JOIN ' : self.ircparse.JOIN,
				'  NOTICE ' : self.ircparse.NOTICE,
				' PRIVMSG ' : self.ircparse.PRIVMSG,
				' MODE ' : self.ircparse.MODE,
				' PART ' : self.ircparse.PART,
			}

			if ':' in row[0] and '@' in row.split(' ', 1)[0]:
				for msgtype in functions:
					if msgtype in row:
						functions[msgtype](row)
			else:
				row = self.refstr(row)
				print(row)
				who, code, row = row.split(' ', 2)
				if code == '353':
					_to, people = row.split(' :', 1)
					if '=' in _to:
						_to, chan = _to.split('=',1)
					elif '@' in _to:
						_to, chan = _to.split('@',1)
					_to = self.refstr(_to)
					chan = self.refstr(chan)
					people = self.refstr(people)
					for person in people.split(' '):
						if person[0] not in ('@', '+'):
							mode = '-'
						else:
							mode = person[0]
						person = person[1:]
						self.channels[chan].join(person, mode)
				elif code == '366':
					_to, chan, row = row.split(' ',2)
					chan = self.refstr(chan)
					print(str(len(list(self.channels[chan].listPeople()))) + ' people in ' + chan,'IRC')

				else:
					pass
					#print 'Unknown starter command',[row]

		self.lockedbuffer = False

	def readable(self):
		return True
	def handle_connect(self):
		print('Connected to ' + str(self.conf['server']), 'IRC')
	def handle_close(self):
		self.close()
	def handle_read(self):
		data = self.recv(8192)
		while self.lockedbuffer:
			sleep(0.01)
		f = open('debug.raw', 'a')
		f.write(str([data]) + '\n')
		f.close()
		for row in data.decode('utf-8').split('\r\n'):
			self.inbuffer.append(row+'\r\n')
	def writable(self):
		return (len(self.buffer) > 0)
	def handle_write(self):
		if not self.is_writable: return

		while self.is_writable:
			pop = self.buffer.pop(0)
			sent = self.send(bytes(pop + '\r\n', 'UTF-8'))
			print('Sent:',pop.strip('\r\n'))
			if len(self.buffer) == 0:
				break
			sleep(1)

		self.is_writable = False
	def _send(self, what):
		self.buffer.append(what + '\r\n')
		self.is_writable = True
	def handle_error(self):
		print('Error, closing socket!', 'IRC')
		traceback.print_exc()
		self.close()
		self.exit = True

	def run(self):
		print('Engine started','IRC')
		#x = start()
		while not self.exit:
			if len(self.inbuffer) > 0:
				self.parse()
			sleep(0.01)
		self.close()

class start(Thread):
	def __init__(self):
		Thread.__init__(self)
		self.start()
	def run(self):
		try:
			asyncore.loop(0.1)
		except asyncore.ExitNow:
			pass

if __name__ == '__main__':
	handle = irc()
	s = start()
	try:
		while len(enumerate()) > 2:
			sleep(1)
	except:
		print('Quitting')
		handle.exit = True
		print('Handle closed')
		asyncore.ExitNow('Server is quitting!')
		print('Asyncore closed')
		relay.exit = True
		print('Relay closed')
sleep(2)
_exit(0)