
import sys
import datetime
import json
import logging
logging.basicConfig(level=logging.CRITICAL)

import psycopg2
import hpfeeds

HOST = 'hpfeeds.honeycloud.net'
PORT = 10000
CHANNELS = ['dionaea.capture', ]
IDENT = ''
SECRET = ''

def main():
    conn = psycopg2.connect("host=localhost dbname=hpfeeds user=username password=pw")
    cur = conn.cursor()

    try:
        hpc = hpfeeds.new(HOST, PORT, IDENT, SECRET)
    except hpfeeds.FeedException, e:
        print >>sys.stderr, 'feed exception:', e
        return 1

    print >>sys.stderr, 'connected to', hpc.brokername

    def on_message(identifier, channel, payload):
        cur.execute("INSERT INTO rawlog (identifier, channel, payload) VALUES (%s, %s, %s)", (identifier, channel, payload))
        conn.commit()

    def on_error(payload):
        print >>sys.stderr, ' -> errormessage from server: {0}'.format(payload)
        hpc.stop()

    hpc.subscribe(CHANNELS)
    try:
        hpc.run(on_message, on_error)
    except hpfeeds.FeedException, e:
        print >>sys.stderr, 'feed exception:', e
    except KeyboardInterrupt:
        pass
    finally:
        cur.close()
        conn.close()
        hpc.close()
    return 0

if __name__ == '__main__':
    try: sys.exit(main())
    except KeyboardInterrupt:sys.exit(0)

