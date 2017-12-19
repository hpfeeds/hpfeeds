#!/usr/bin/python

import sys
import logging
logging.basicConfig(level=logging.WARNING)
from  gridfs  import GridFS
import hpfeeds
import pymongo
import ast
import datetime
import md5

HOST = '127.0.0.1'
PORT = 10000
CHANNELS = ['dionaea.connections', 'geoloc.events','dionaea.dcerpcrequests','dionaea.shellcodeprofiles','mwbinary.dionaea.sensorunique','dionaea.capture']
IDENT = 'ww3ee@hp1'
SECRET = '7w35rippuhx7704h'

# Required
MONGOHOST = '127.0.0.1'
MONGOPORT = 27017
MONGODBNAME = 'dionaea'
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

    insertCon = pymongo.Connection(host="localhost",port=27017)
    db = None
    collection = None
    
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
                db = insertCon['dionaea']
                collection = db['connection']
                collection.insert(msg)
        elif channel == 'geoloc.events':
            try:
                payload_python = str(payload)
                msg = ast.literal_eval(payload_python.replace("null", "None"))
            except:
                print 'exception processing geoloc.events', repr(payload)
            else:
                msg['time'] = datetime.datetime.strptime(msg['time'], "%Y-%m-%d %H:%M:%S")
                print 'inserting...', msg
                db = insertCon['geoloc']
                collection =  db['events']
                collection.insert(msg)
        elif channel == 'dionaea.dcerpcrequests':
            try:
                payload_python = str(payload)
                msg = ast.literal_eval(payload_python.replace("null", "None"))
            except:
                print 'exception processing dionaea.dcerpcrequests', repr(payload)
            else:
                dt = datetime.datetime.now()
                msg['time'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                print 'inserting...', msg
                db = insertCon['dionaea']
                collection = db['dcerpcrequests']
                collection.insert(msg)
        elif channel == 'dionaea.shellcodeprofiles':
            try:
                payload_python = str(payload)
                msg = ast.literal_eval(payload_python.replace("null", "None"))
            except:
                print 'exception processing dionaea.shellcodeprofiles', repr(payload)
            else:
                dt = datetime.datetime.now()
                msg['time'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                print 'inserting...', msg
                db = insertCon['dionaea']
                collection = db['shellcodeprofiles']
                collection.insert(msg)
        elif channel == 'mwbinary.dionaea.sensorunique' :
            try:
                payload_python = str(payload)
            except:
                print 'exception processing mwbinary.dionaea.sensorunique', repr(payload)
            else:
                hash = md5.new()
                hash.update(payload_python)
                msg = hash.hexdigest()
                print 'inserting mwbinary...', msg
                
                db = insertCon['dionaea']
                gfsDate=GridFS(db)
                gfsDate.put(payload_python,filename=msg)
        elif channel == 'dionaea.capture':
            try:
                payload_python = str(payload)
                msg = ast.literal_eval(payload_python.replace("null", "None"))
            except:
                print 'exception processing dionaea.capture', repr(payload)
            else:
                dt = datetime.datetime.now()
                msg['time'] = dt.strftime('%Y-%m-%d %H:%M:%S')
                print 'inserting...', msg
                db = insertCon['dionaea']
                collection = db['capture']
                collection.insert(msg)        
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

