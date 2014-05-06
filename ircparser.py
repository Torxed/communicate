#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
from time import sleep, strftime, localtime, time
from random import randint

class ircparsers():
	def __init__(self, sender, conf, channels):
		self.conf = conf
		self.send = sender
		self.channels = channels

	def refstr(self, what):
		while len(what) > 0 and what[-1] in ('\r', '\n', ':', ' ', '	'):
			what = what[:-1]
		while len(what) > 0 and what[0] in ('\r', '\n', ':', ' ', '	'):
			what = what[1:]
		return what

	def MODE(self, data):
		who, msgtype, channel, msg = data.split(' ', 3)
		who, host = self.refstr(who).split('!',1)
		channel = self.refstr(channel)
		if channel == self.conf['nickname']:
			return True

		mode, towho = msg.split(' ',1)
		if '+o' in mode:
			mode = '@'
		elif '+v' in mode:
			mode = '+'
		else:
			mode = '-'
		self.channels[channel].mode(who, mode)
			#self.channels[channel]['people'][towho] = mode

	def PRIVMSG(self, data):
		# :DoXiD!~na@c-9ac3e355.41-5-64736c11.cust.bredbandsbolaget.se PRIVMSG #DHSupport :Test
		who, msgtype, channel, msg = data.split(' ', 3)
		who, host = self.refstr(who).split('!')
		channel = self.refstr(channel)
		msg = msg[1:]
		replychan = channel

		self.channels[channel].sad(who, msg)

	def NOTICE(self, data):
		return None

	def PART(self, data):
		# :DoXiD!~DoXiD@109-124-175-121.customer.t3.se PART #kablamo
		who, msgtype, channel = data.split(' ', 2)
		if '!' in who:
			who, host = who.split('!', 1)
			who = self.refstr(who)
			self.channels[channel].part(who)

	def JOIN(self, data):
		who, msgtype, channel = data.split(' ', 2)
		channel = self.refstr(channel)

		if '!' in who:
			who, host = who.split('!', 1)
			who = self.refstr(who)
			if not who[0] in ('@', '+'):
				mode = '-'
			else:
				mode = who[0]
				who = who.replace('@', '').replace('+','')
			self.channels[channel].join(who, mode)
		return None
