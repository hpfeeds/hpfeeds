#!/usr/bin/env python

import sys

import struct
import hashlib
import collections
import random

import logging
logging.basicConfig(level=logging.INFO)

from evnet import loop, unloop, listenplain, EventGen
from evnet.mongodb import MongoConn

FBIP = '0.0.0.0'
FBPORT = 10000
FBNAME = '@hp2'
MONGOIP = '127.0.0.1'
MONGOPORT = 27017

OP_ERROR	= 0
OP_INFO		= 1
OP_AUTH		= 2
OP_PUBLISH	= 3
OP_SUBSCRIBE	= 4
OP_UNSUBSCRIBE	= 5

MAXBUF = 10* (1024**2)
SIZES = {
	OP_ERROR: 5+MAXBUF,
	OP_INFO: 5+256+20,
	OP_AUTH: 5+256+20,
	OP_PUBLISH: 5+MAXBUF,
	OP_SUBSCRIBE: 5+256*2,
	OP_UNSUBSCRIBE: 5+256*2,
}

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
		if ml > SIZES.get(opcode, MAXBUF):
			raise BadClient('Not respecting MAXBUF.')

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
		p = self.db.query('hpfeeds.auth_key', {'identifier': str(ident)}, limit=1)
		p._when(self.checkauth, hash)

		def dbexc(e):
			logging.critical('Database query exception. {0}'.format(e))
			self.error('Database query exception.')
		
		p._except(dbexc)

		self.delay = True

	def checkauth(self, r, hash):
		if len(r) > 0:
			akobj = r[0]
			akhash = hashlib.sha1('{0}{1}'.format(self.rand, akobj['secret'])).digest()
			if akhash == hash:
				self.pubchans.update(akobj.get('publish', []))
				self.subchans.update(akobj.get('subscribe', []))
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

	def may_publish(self, chan):
		return chan in self.pubchans

	def may_subscribe(self, chan):
		return chan in self.subchans

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

					if not self.may_publish(chan):
						self.error('accessfail.')
						continue
					
					self._event('publish', self, chan, data)
				elif opcode == OP_SUBSCRIBE:
					rest = buffer(data, 0)
					ident, chan = rest[1:1+ord(rest[0])], rest[1+ord(rest[0]):]

					if not ident in self.idents:
						self.error('identfail.')
						continue

					checkchan = chan
					if chan.endswith('..broker'): checkchan = chan.rsplit('..broker', 1)[0]

					if not self.may_subscribe(checkchan):
						self.error('accessfail.')
						continue

					self._event('subscribe', self, chan, ident)
				elif opcode == OP_UNSUBSCRIBE:
					rest = buffer(data, 0)
					ident, chan = rest[1:1+ord(rest[0])], rest[1+ord(rest[0]):]

					if not ident in self.idents:
						self.error('identfail.')
						continue

					if not self.may_subscribe(chan):
						self.error('accessfail.')
						continue

					self._event('unsubscribe', self, chan, ident)
				elif opcode == OP_AUTH:
					rest = buffer(data, 0)
					ident, hash = rest[1:1+ord(rest[0])], rest[1+ord(rest[0]):]
					self.auth(ident, hash)
					if self.delay:
						return

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

	def msgpublish(self, ident, chan, data):
		return self.msghdr(OP_PUBLISH, struct.pack('!B', len(ident)) + ident + struct.pack('!B', len(chan)) + chan + data)

	def publish(self, ident, chan, data):
		self.conn.write(self.msgpublish(ident, chan, data))

class FeedBroker(object):
	def __init__(self):
		self.ready = False

		self.db = None
		self.initdb()

		self.listener = listenplain(host=FBIP, port=FBPORT)
		self.listener._on('close', self._lclose)
		self.listener._on('connection', self._newconn)

		self.connections = set()
		self.subscribermap = collections.defaultdict(list)
		self.conn2chans = collections.defaultdict(list)

	def initdb(self):
		self.db = MongoConn(MONGOIP, MONGOPORT)
		self.db._on('ready', self._dbready)
		self.db._on('close', self._dbclose)

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
		fc._on('unsubscribe', self._unsubscribe)
		fc._on('publish', self._publish)

	def _connclose(self, c):
		self.connections.remove(c)
		for chan in self.conn2chans[c]:
			self.subscribermap[chan].remove(c)
			for ident in c.idents:
				self._brokerchan(c, chan, ident, 0)

	def _publish(self, c, chan, data):
		logging.debug('broker publish to {0} by {1}'.format(chan, c.addr))
		for c2 in self.subscribermap[chan]:
			if c2 == c: continue
			c2.forward(data)
		
	def _subscribe(self, c, chan, ident):
		logging.debug('broker subscribe to {0} by {2} @ {1}'.format(chan, c.addr, ident))
		self.subscribermap[chan].append(c)
		self.conn2chans[c].append(chan)
		self._brokerchan(c, chan, ident, 1)
	
	def _unsubscribe(self, c, chan, ident):
		logging.debug('broker unsubscribe to {0} by {1}'.format(chan, c.addr))
		self.subscribermap[chan].remove(c)
		self.conn2chans[c].remove(chan)
		self._brokerchan(c, chan, ident, 0)

	def _brokerchan(self, c, chan, ident, subscribe=0):
		data = 'join' if subscribe else 'leave'
		if self.subscribermap[chan+'..broker']:
			for c2 in self.subscribermap[chan+'..broker']:
				if c2 == c: continue
				c2.publish(ident, chan+'..broker', data)

def main():
	fb = FeedBroker()

	loop()
	return 0
 
if __name__ == '__main__':
	sys.exit(main())

