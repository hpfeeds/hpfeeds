#!/usr/bin/python

import sys
import logging
logging.basicConfig(level=logging.WARNING)

import traceback
import json
import hpfeeds

HOST = '192.168.168.113'
PORT = 10000
CHANNELS = ['dionaea.capture', ]
IDENT = 'ident'
SECRET = 'secret'

RELAYCHAN = 'dionaea.capture.anon'

def main():
    hpc = hpfeeds.new(HOST, PORT, IDENT, SECRET)
    print >>sys.stderr, 'connected to', hpc.brokername

    def on_message(ident, channel, payload):
        try:
            dec = json.loads(str(payload))
            del dec['daddr']
            dec['identifier'] = ident
            enc = json.dumps(dec)
        except:
            traceback.print_exc()
            print >>sys.stderr, 'forward error for message from {0}.'.format(ident)
            return

        hpc.publish(RELAYCHAN, enc)

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

