#!/usr/bin/env python

import sys

import struct
import hashlib
import collections
import random

import logging
logging.basicConfig(level=logging.DEBUG)

from evnet import loop, unloop, listenplain, EventGen
from evnet.mongodb import MongoConn

FBIP = '0.0.0.0'
FBPORT = 10001
FBNAME = '@hp1'
MONGOIP = '127.0.0.1'
MONGOPORT = 27017

OP_ERROR	= 0
OP_INFO		= 1
OP_AUTH		= 2
OP_PUBLISH	= 3
OP_SUBSCRIBE	= 4

class BadClient(Exception):
	pass

class FeedUnpack(object):
	def __init__(self):
		self.buf = bytearray()
	def __iter__(self):
		return self
	def next(self):
		return self.unpack()
	def feed(self, data):
		self.buf.extend(data)
	def unpack(self):
		if len(self.buf) < 5:
			raise StopIteration('No message.')

		ml, opcode = struct.unpack('!iB', buffer(self.buf,0,5))
		if len(self.buf) < ml:
			raise StopIteration('No message.')
		
		data = bytearray(buffer(self.buf, 5, ml-5))
		del self.buf[:ml]
		return opcode, data


class FeedConn(EventGen):
	def __init__(self, conn, addr, db):
		EventGen.__init__(self)
		self.conn = conn
		self.addr = addr
		self.db = db
		self.pubchans = set()
		self.subchans = set()
		self.idents = set()
		self.delay = False

		self.rand = struct.pack('<I', random.randint(2**31,2**32-1))
		self.fu = FeedUnpack()

		conn._on('read', self.io_in)
		conn._on('close', self.closed)

		self.sendinfo()

	def sendinfo(self):
		self.conn.write(self.msginfo())

	def auth(self, ident, hash):
		p = self.db.query('hpfeeds.authkey', {'identifier': str(ident)}, limit=1)
		p._when(self.checkauth, hash)

		def dbexc(e):
			logging.critical('Database query exception. {0}'.format(e))
			self.error('Database query exception.')
		
		p._except(dbexc)

		self.delay = True

	def checkauth(self, r, hash):
		if len(r) > 0:
			akobj = r[0]
			akhash = hashlib.sha1('{0}{1}'.format(self.rand, akobj['secret'])).hexdigest()
			if akhash == hash:
				self.pubchans.update(akobj['publish'])
				self.subchans.update(akobj['subscribe'])
				self.idents.add(akobj['identifier'])
				logging.info('Auth success by {0}.'.format(akobj['identifier']))
			else:
				self.error('authfail.')
				logging.info('Auth failure by {0}.'.format(akobj['identifier']))
		else:
			self.error('authfail.')

		self.delay = False
		self.io_in(b'')
	
	def closed(self, reason):
		logging.debug('Connection closed, {0}'.format(reason))
		self._event('close', self)

	def io_in(self, data):
		self.fu.feed(data)
		if self.delay:
			return
		try:
			for opcode, data in self.fu:
				if opcode == OP_PUBLISH:
					rest = buffer(data, 0)
					ident, rest = rest[1:1+ord(rest[0])], buffer(rest, 1+ord(rest[0]))
					chan, rest = rest[1:1+ord(rest[0])], buffer(rest, 1+ord(rest[0]))

					if not ident in self.idents:
						self.error('identfail.')
						continue

					if not chan in self.pubchans:
						self.error('accessfail.')
						continue
					
					self._event('publish', self, chan, data)
				elif opcode == OP_SUBSCRIBE:
					rest = buffer(data, 0)
					ident, chan = rest[1:1+ord(rest[0])], rest[1+ord(rest[0]):]

					if not ident in self.idents:
						self.error('identfail.')
						continue

					if not chan in self.subchans:
						self.error('accessfail.')
						continue

					self._event('subscribe', self, chan)
				elif opcode == OP_AUTH:
					rest = buffer(data, 0)
					ident, hash = rest[1:1+ord(rest[0])], rest[1+ord(rest[0]):]
					self.auth(ident, hash)

		except BadClient:
			self.conn.close()
			logging.warn('Disconnecting bad client: {0}'.format(self.addr))

	def forward(self, data):
		self.conn.write(self.msghdr(OP_PUBLISH, data))

	def error(self, emsg):
		self.conn.write(self.msgerror(emsg))

	def msgerror(self, emsg):
		return self.msghdr(OP_ERROR, emsg)

	def msginfo(self):
		return self.msghdr(OP_INFO, '{0}{1}{2}'.format(chr(len(FBNAME)%0xff), FBNAME, self.rand))

	def msghdr(self, op, data):
		return struct.pack('!iB', 5+len(data), op) + data


class FeedBroker(object):
	def __init__(self):
		self.ready = False

		self.db = None
		self.db = MongoConn(MONGOIP, MONGOPORT)
		self.db._on('ready', self._dbready)
		self.db._on('close', self._dbclose)

		self.listener = listenplain(host=FBIP, port=FBPORT)
		self.listener._on('close', self._lclose)
		self.listener._on('connection', self._newconn)

		self.listener2 = listenplain(host=FBIP, port=FBPORT+1)
		self.listener2._on('close', self._lclose)
		self.listener2._on('connection', self._newconnplain)

		self.connections = set()
		self.subscribermap = collections.defaultdict(list)
		self.conn2chans = collections.defaultdict(list)

	def _dbready(self):
		self.ready = True
		logging.info('Database ready.')

	def _dbclose(self, e):
		logging.critical('Database connection closed ({0}). Exiting.'.format(e))
		unloop()

	def _lclose(self, e):
		logging.critical('Listener closed ({0}). Exiting.'.format(e))
		unloop()

	def _newconn(self, c, addr):
		logging.debug('Connection from {0}.'.format(addr))
		fc = FeedConn(c, addr, self.db)
		self.connections.add(fc)
		fc._on('close', self._connclose)
		fc._on('subscribe', self._subscribe)
		fc._on('publish', self._publish)

	def _newconnplain(self, c, addr):
		logging.debug('Connection from {0}.'.format(addr))
		fc = FeedConnPlain(c, addr, self.db)
		self.connections.add(fc)
		fc._on('close', self._connclose)
		fc._on('subscribe', self._subscribe)
		fc._on('publish', self._publish)

	def _connclose(self, c):
		self.connections.remove(c)
		for chan in self.conn2chans[c]:
			self.subscribermap[chan].remove(c)

	def _publish(self, c, chan, data):
		logging.debug('broker publish to {0} by {1}'.format(chan, c.addr))
		for c2 in self.subscribermap[chan]:
			if c2 == c:
				continue
			c2.forward(data)
		
	def _subscribe(self, c, chan):
		logging.debug('broker subscribe to {0} by {1}'.format(chan, c.addr))
		self.subscribermap[chan].append(c)
		self.conn2chans[c].append(chan)

def main():
	fb = FeedBroker()

	loop()
	return 0
 
if __name__ == '__main__':
	sys.exit(main())

