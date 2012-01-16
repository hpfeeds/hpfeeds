
import sys
import datetime
import json
import logging
logging.basicConfig(level=logging.CRITICAL)

import hpfeeds

HOST = 'hpfeeds.honeycloud.net'
PORT = 10000
CHANNELS = ['thug.files',]
IDENT = ''
SECRET = ''
OUTFILE = './grab.log'
OUTDIR = './files/'

def main():
	try: outfd = open(OUTFILE, 'a')
	except:
		print >>sys.stderr, 'could not open output file for message log.'
		return 1

	if not os.path.exists(OUTDIR): os.mkdir(OUTDIR)

	hpc = hpfeeds.new(HOST, PORT, IDENT, SECRET)
	print >>sys.stderr, 'connected to', hpc.brokername

	def on_message(identifier, channel, payload):
		try: decoded = json.loads(str(payload))
		except: decoded = {'raw': payload}

		if not 'sha1' in decoded or not 'data' in decoded:
			print >>sys.stderr, "Message received does not contain hash or data :( - ignoring it..."
		else:
			print >>sys.stderr, "Got a message with sha1 and data"

			csv = ', '.join(['{0}={1}'.format(i,decoded[i]) for i in ['sha1', 'type', 'md5']])
			outmsg = '{0} PUBLISH chan={1}, identifier={2}, {3}'.format(
				datetime.datetime.now().ctime(), chan, ident, csv
			)

			print >>outfd, outmsg

			# now store the file itself
			filedata = decoded['data'].decode('base64')
			fpath = os.path.join(opts.outdir, decoded['sha1'])
			try:
				open(fpath, 'wb').write(filedata)
			except:
				print >>outfd, '{0} ERROR could not write to {1}'.format(datetime.datetime.now().ctime(), fpath)
			outfd.flush()

	def on_error(payload):
		print >>sys.stderr, ' -> errormessage from server: {0}'.format(payload)
		hpc.stop()

	hpc.subscribe(CHANNELS)
	hpc.run(on_message, on_error)
	hpc.close()
	return 0

if __name__ == '__main__':
	try: sys.exit(main())
	except KeyboardInterrupt:sys.exit(0)

