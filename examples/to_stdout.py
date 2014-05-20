#!/opt/hpfeeds/env/bin/python

import sys
import logging
logging.basicConfig(level=logging.WARNING)
import hpfeeds

def main():
    if len(sys.argv) < 5:
        print >> sys.stderr, "Usage: python %s <host> <port> <ident> <secret> <channel,channel2,channel3,...>"%(sys.argv[0])
        sys.exit(1)

    HOST, PORT, IDENT, SECRET, CHANNELS = [arg.encode("utf-8") for arg in sys.argv[1:6]]
    CHANNELS = CHANNELS.split(",")
    PORT = int(PORT)

    hpc = hpfeeds.new(HOST, PORT, IDENT, SECRET)
    print >>sys.stderr, 'connected to', hpc.brokername
    
    def on_message(identifier, channel, payload):
        try:
            payload = str(payload).strip()
            print "ident=%s, channel=%s, payload='%s'"%(identifier, channel, payload)
        except Exception, e:
            print "Error", e

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
