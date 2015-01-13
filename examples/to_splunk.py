#!/opt/hpfeeds/env/bin/python

import sys
import logging
logging.basicConfig(level=logging.WARNING)
import hpfeeds
import json
outstream = sys.stdout
import datetime

def main():
    global outstream
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
            record = json.loads(payload)
            if 'source' in record:
                record['src'] = record['source']
                del record['source']
            print >>outstream, unicode(datetime.datetime.utcnow()) + u' '+ u' '.join([ u'='.join([unicode(k),unicode(v)]) for k,v in record.items()])
            outstream.flush()
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

