
import os
import sys
import datetime
import json
import select
import traceback
import logging
logging.basicConfig(level=logging.CRITICAL)

import hpfeeds

HOST = 'hpfeeds.honeycloud.net'
PORT = 10000
CHANNELS = ['test.channel',]
IDENT = ''
SECRET = ''

def main():
    hpc = hpfeeds.new(HOST, PORT, IDENT, SECRET)
    print >>sys.stderr, 'connected to', hpc.brokername

    def on_message(identifier, channel, payload):
        try: decoded = json.loads(str(payload))
        except: decoded = {'raw': payload}

        print 'incoming message from {0} on channel {1}, length {2}'.format(identifier, channel, len(payload))

    def on_error(payload):
        print >>sys.stderr, ' -> errormessage from server: {0}'.format(payload)
        hpc.stop()

    #hpc.subscribe(CHANNELS)

    hpc.s.settimeout(0.01)

    while True:
        rrdy, wrdy, xrdy = select.select([hpc.s, sys.stdin], [], [])
        if hpc.s in rrdy:
            try: hpc.run(on_message, on_error)
            except socket.timeout: pass
        if sys.stdin in rrdy:
            try: l = sys.stdin.readline()
            except: traceback.print_exc()
            else:
                if l.strip(): hpc.publish(CHANNELS, l)
    
    print 'quit.'
    hpc.close()
    return 0

if __name__ == '__main__':
    try: sys.exit(main())
    except KeyboardInterrupt:sys.exit(0)

