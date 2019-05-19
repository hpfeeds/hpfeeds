
import sys
import datetime
import json
import logging
logging.basicConfig(level=logging.CRITICAL)
from time import sleep
import hpfeeds

HOST = 'hpfeeds.honeycloud.net'
PORT = 10000
CHANNELS = ['dionaea.capture',]
IDENT = ''
SECRET = ''
OUTFILE = 'hpfeedcsv.log'

def main():
    try: outfd = open(OUTFILE, 'a')
    except:
        print >>sys.stderr, 'could not open output file for message log.'
        return 1

    def on_message(identifier, channel, payload):
        try: decoded = json.loads(str(payload))
        except: decoded = {'raw': payload}

        csv = ', '.join(['{0}={1}'.format(i,j) for i,j in decoded.items()])
        outmsg = '{0} PUBLISH chan={1}, identifier={2}, {3}'.format(
            datetime.datetime.now().ctime(), channel, identifier, csv
        )

        print >>outfd, outmsg
        outfd.flush()

    def on_error(payload):
        print >>sys.stderr, ' -> errormessage from server: {0}'.format(payload)
        hpc.stop()

    hpc = hpfeeds.new(HOST, PORT, IDENT, SECRET, reconnect=True)
    print >>sys.stderr, 'connected to', hpc.brokername
    hpc.subscribe(CHANNELS)
    hpc.run(on_message, on_error)
    hpc.close()
    return 0

if __name__ == '__main__':
    try: sys.exit(main())
    except KeyboardInterrupt:sys.exit(0)

