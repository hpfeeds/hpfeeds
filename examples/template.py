#!/usr/bin/python

import sys
import logging
logging.basicConfig(level=logging.WARNING)

import hpfeeds

HOST = '192.168.168.113'
PORT = 10000
CHANNELS = ['dionaea.shellcodeprofiles', 'dionaea.capture', 'thug.events', ]
IDENT = 'ident'
SECRET = 'secret'

def main():
    hpc = hpfeeds.new(HOST, PORT, IDENT, SECRET)
    print >>sys.stderr, 'connected to', hpc.brokername

    def on_message(identifier, channel, payload):
        print 'msg', identifier, channel, payload

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

