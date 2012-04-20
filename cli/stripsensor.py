#!/usr/bin/env python

import sys
import struct
import hashlib
import random
import json
import traceback

import logging
logging.basicConfig(level=logging.DEBUG)

from evnet import loop, unloop, connectplain

import hpfeeds

FBIP = 'hpfeeds.honeycloud.net'
FBPORT = 10000
IDENT = ''
SECRET = ''

class FeedConn(object):
	def __init__(self):
		self.fu = hpfeeds.FeedUnpack()
		self.conn = connectplain(FBIP, FBPORT)
		self.conn._on('read', self.io_in)
		self.conn._on('close', self.closed)

	def closed(self, reason):
		logging.debug('Connection closed, {0}'.format(reason))
		unloop()

	def io_in(self, data):
		self.fu.feed(data)
		for opcode, data in self.fu:
			if opcode == hpfeeds.OP_INFO:
				rest = buffer(data, 0)
				name, rest = rest[1:1+ord(rest[0])], buffer(rest, 1+ord(rest[0]))
				rand = str(rest)
				self.conn.write(hpfeeds.msgauth(rand, IDENT, SECRET))
				self.conn.write(hpfeeds.msgsubscribe(IDENT, 'dionaea.capture'))
			elif opcode == hpfeeds.OP_PUBLISH:
				rest = buffer(data, 0)
				ident, rest = rest[1:1+ord(rest[0])], buffer(rest, 1+ord(rest[0]))
				chan, content = rest[1:1+ord(rest[0])], buffer(rest, 1+ord(rest[0]))
				#logging.debug('publish to {0} by {1}'.format(chan, ident))
				self.anonforward(ident, chan, bytes(content))
			elif opcode == hpfeeds.OP_ERROR:
				logging.critical('errormessage from server: {0}'.format(data))

	def anonforward(self, ident, chan, content):
		try:
			dec = json.loads(content)
			del dec['daddr']
			dec['identifier'] = ident
			enc = json.dumps(dec)
		except:
			traceback.print_exc()
			logging.critical('forward error for message from {0}.'.format(ident))
			return

		self.conn.write(hpfeeds.msgpublish(IDENT, 'dionaea.capture.anon', enc))


def main():
	fbc = FeedConn()
	loop()
	return 0
 
if __name__ == '__main__':
	try:
		sys.exit(main())
	except KeyboardInterrupt:
		sys.exit(0)

