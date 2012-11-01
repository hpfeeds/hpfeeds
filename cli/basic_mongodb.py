#!/usr/bin/python

import sys
import logging
logging.basicConfig(level=logging.WARNING)

import hpfeeds
import pymongo
import ast
import datetime

HOST = '192.168.168.113'
PORT = 10000
CHANNELS = ['dionaea.connections', 'geoloc.events']
IDENT = 'ident'
SECRET = 'secret'

# Required
MONGOHOST = '127.0.0.1'
MONGOPORT = 27017
MONGODBNAME = 'hpfeeds-test'
# Optional
MONGOUSER = ''
MONGOPWD = ''

def get_db(host, port, name, user = '', passwd = ''):
        dbconn = pymongo.Connection(host, port)
        db = pymongo.database.Database(dbconn, name)
	if user != '' or passwd != '':
        	db.authenticate(user, passwd)
        return db


def main():
	hpc = hpfeeds.new(HOST, PORT, IDENT, SECRET)
	print >>sys.stderr, 'connected to', hpc.brokername

	db = get_db(MONGOHOST, MONGOPORT, MONGODBNAME, MONGOUSER, MONGOPWD)

	def on_message(identifier, channel, payload):
		if channel == 'dionaea.connections':
			try:
				msg = ast.literal_eval(str(payload))
			except:
				print 'exception processing dionaea.connections event', repr(payload)
			else:
				msg["time"] = datetime.datetime.utcfromtimestamp(msg['time'])
				msg['rport'] = int(msg['rport'])
				msg['lport'] = int(msg['lport'])
				print 'inserting...', msg
				db['dionaea'].insert(msg)
		elif channel == 'geoloc.events':
			try:
				payload_python = str(payload)
				msg = ast.literal_eval(payload_python.replace("null", "None"))
			except:
				print 'exception processing geoloc.events', repr(payload)
			else:
				msg['time'] = datetime.datetime.strptime(msg['time'], "%Y-%m-%d %H:%M:%S")
				print 'inserting...', msg
				db['geoloc'].insert(msg)


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

