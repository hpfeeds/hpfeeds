
import os
import sys
import struct
import socket
import optparse
import hashlib
import datetime
import string
import json

OP_ERROR	= 0
OP_INFO		= 1
OP_AUTH		= 2
OP_PUBLISH	= 3
OP_SUBSCRIBE	= 4

def log(msg):
	sys.stderr.write('[feedcli] {0}\n'.format(msg))

def msghdr(op, data):
	return struct.pack('!iB', 5+len(data), op) + data
def msgpublish(ident, chan, data):
	if isinstance(data, str):
		data = data.encode('latin1')
	return msghdr(OP_PUBLISH, struct.pack('!B', len(ident)) + ident + struct.pack('!B', len(chan)) + chan + data)
def msgsubscribe(ident, chan):
	return msghdr(OP_SUBSCRIBE, struct.pack('!B', len(ident)) + ident + chan)
def msgauth(rand, ident, secret):
	hash = hashlib.sha1(rand+secret).digest()
	return msghdr(OP_AUTH, struct.pack('!B', len(ident)) + ident + hash)

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

def main(opts, action, pubdata=None):
	#log('Connecting to feed broker...')

	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.settimeout(3)
	try:
		s.connect((opts.host, opts.port))
	except:
		log('could not connect to broker.')
		return 1

	outfd = sys.stdout
	if opts.output:
		try: outfd = open(opts.output, 'a')
		except:
			log('could not open output file for message log.')
			return 1

	if not opts.outdir: opts.outdir = './files/'
	if not os.path.exists(opts.outdir): os.mkdir(opts.outdir)

	s.settimeout(None)
	unpacker = FeedUnpack()
	d = s.recv(1024)

	published = False

	while d and not published:
		unpacker.feed(d)
		for opcode, data in unpacker:
			if opcode == OP_INFO:
				rest = buffer(data, 0)
				name, rest = rest[1:1+ord(rest[0])], buffer(rest, 1+ord(rest[0]))
				rand = str(rest)

				s.send(msgauth(rand, opts.ident, opts.secret))
				for c in opts.channels:
					if action == 'publish':
						s.send(msgpublish(opts.ident, c, pubdata))
						published = True
						s.settimeout(0.1)
					else:
						s.send(msgsubscribe(opts.ident, c))
			elif opcode == OP_PUBLISH:
				rest = buffer(data, 0)
				ident, rest = rest[1:1+ord(rest[0])], buffer(rest, 1+ord(rest[0]))
				chan, content = rest[1:1+ord(rest[0])], buffer(rest, 1+ord(rest[0]))

				try: decoded = json.loads(str(content))
				except: decoded = {'raw': content}

				if not 'sha1' in decoded or not 'data' in decoded:
					print >>sys.stderr, "Message received does not contain hash or data :( - ignoring it..."
				else:
					print >>sys.stderr, "Got a message with sha1 and data"

					csv = ', '.join(['{0}={1}'.format(i,decoded[i]) for i in ['sha1', 'type', 'md5']])
					outmsg = '{0} PUBLISH chan={1}, identifier={2}, {3}'.format(
						datetime.datetime.now().ctime(), chan, ident, csv
					)

					print >>outfd, outmsg
					outfd.flush()

					# now store the file itself
					filedata = decoded['data'].decode('base64')
					fpath = os.path.join(opts.outdir, decoded['sha1'])
					try:
						open(fpath, 'wb').write(filedata)
					except:
						print >>outfd, '{0} ERROR could not write to {1}'.format(datetime.datetime.now().ctime(), fpath)
						outfd.flush()

			elif opcode == OP_ERROR:
				log('errormessage from server: {0}'.format(data))

		try:
			d = s.recv(1024)
		except KeyboardInterrupt:
			break
		except socket.timeout:
			break

	s.close()
	return 0

def opts():
	usage = "usage: %prog [options] publish|subscribe <publish_data>"
	parser = optparse.OptionParser(usage=usage)
	parser.add_option("-c", "--chan",
		action="append", dest='channels', nargs=1, type='string',
		help="channel (can be used multiple times)")
	parser.add_option("-i", "--ident",
		action="store", dest='ident', nargs=1, type='string',
		help="authkey identifier")
	parser.add_option("-s", "--secret",
		action="store", dest='secret', nargs=1, type='string',
		help="authkey secret")
	parser.add_option("--host",
		action="store", dest='host', nargs=1, type='string',
		help="broker host")
	parser.add_option("-p", "--port",
		action="store", dest='port', nargs=1, type='int',
		help="broker port")
	parser.add_option("-o", "--output",
		action="store", dest='output', nargs=1, type='string',
		help="log filename")
	parser.add_option("-d", "--outdir",
		action="store", dest='outdir', nargs=1, type='string',
		help="directory for files")

	options, args = parser.parse_args()

	if len(args) < 1 or args[0] not in ['subscribe', 'publish'] or None in options.__dict__.values():
		parser.print_help()
		parser.error('You need to give "subscribe" or "publish" as <action>.')

	action = args[0]
	data = None
	if action == 'publish':
		data = ' '.join(args[1:])

	return options, action, data

if __name__ == '__main__':
	options, action, data = opts()
	try:
		sys.exit(main(options, action, pubdata=data))
	except KeyboardInterrupt:
		sys.exit(0)

