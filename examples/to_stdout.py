#!/opt/hpfeeds/env/bin/python

import sys
import logging
logging.basicConfig(level=logging.WARNING)
import hpfeeds

def main():
    outstream = sys.stdout

    if len(sys.argv) < 5:
        print >> sys.stderr, "Usage: python %s <host> <port> <ident> <secret> <channel,channel2,channel3,...> [logfile]"%(sys.argv[0])
        sys.exit(1)

    HOST, PORT, IDENT, SECRET, CHANNELS = [arg.encode("utf-8") for arg in sys.argv[1:6]]
    CHANNELS = CHANNELS.split(",")
    PORT = int(PORT)
    
    if len(sys.argv) > 6:
        outstream = open(sys.argv[6], "a")

    hpc = hpfeeds.new(HOST, PORT, IDENT, SECRET)
    print >>sys.stderr, 'connected to', hpc.brokername
    
    def on_message(identifier, channel, payload):
        try:
            payload = str(payload).strip()
            print >>outstream, "ident=%s, channel=%s, payload=%s"%(identifier, channel, payload)
        except Exception, e:
            print >> sys.stderr, "Error", e

    def on_error(payload):
        print >>sys.stderr, ' -> errormessage from server: {0}'.format(payload)
        hpc.stop()
        outstream.close()

    hpc.subscribe(CHANNELS)
    hpc.run(on_message, on_error)
    hpc.close()
    outstream.close()
    return 0

if __name__ == '__main__':
    try: sys.exit(main())
    except KeyboardInterrupt:
        outstream.close()
        sys.exit(0)
