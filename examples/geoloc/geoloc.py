import sys
import datetime
import logging
logging.basicConfig(level=logging.CRITICAL)

import hpfeeds
from processors import *

import GeoIP
import traceback

HOST = 'localhost'
PORT = 10000
CHANNELS = [
    'amun.events',
    'dionaea.connections',
    'dionaea.capture',
    'glastopf.events',
    'beeswarm.hive',
    'kippo.sessions',
    'cowrie.sessions',
    'conpot.events',
    'snort.alerts'
    'wordpot.events',
    'shockpot.events',
    'p0f.events',
    'suricata.events',
    'elastichoney.events',
]
GEOLOC_CHAN = 'geoloc.events'
IDENT = ''
SECRET = ''

if len(sys.argv) > 1:
    print >>sys.stderr, "Parsing config file: %s"%sys.argv[1]
    import json
    config = json.load(file(sys.argv[1]))
    HOST        = config["HOST"]
    PORT        = config["PORT"]
    # hpfeeds protocol has trouble with unicode, hence the utf-8 encoding here
    CHANNELS    = [c.encode("utf-8") for c in config["CHANNELS"]]
    GEOLOC_CHAN = config["GEOLOC_CHAN"].encode("utf-8")
    IDENT       = config["IDENT"].encode("utf-8")
    SECRET      = config["SECRET"].encode("utf-8")
else:
    print >>sys.stderr, "Warning: no config found, using default values for hpfeeds server"

PROCESSORS = {
    'amun.events': [amun_events],
    'glastopf.events': [glastopf_event,],
    'dionaea.capture': [dionaea_capture,],
    'dionaea.connections': [dionaea_connections,],
    'beeswarm.hive': [beeswarm_hive,],
    'kippo.sessions': [kippo_sessions,],
    'cowrie.sessions': [cowrie_sessions,],
    'conpot.events': [conpot_events,],
    'snort.alerts': [snort_alerts,],
    'wordpot.events': [wordpot_event,],
    'shockpot.events': [shockpot_event,],
    'p0f.events': [p0f_event,],
    'suricata.events': [suricata_events,],
    'elastichoney.events': [elastichoney_events,],
}

def main():
    import socket
    gi = {}
    gi[socket.AF_INET] = GeoIP.open("/opt/GeoLiteCity.dat",GeoIP.GEOIP_STANDARD)
    gi[socket.AF_INET6] = GeoIP.open("/opt/GeoLiteCityv6.dat",GeoIP.GEOIP_STANDARD)

    try:
        hpc = hpfeeds.new(HOST, PORT, IDENT, SECRET)
    except hpfeeds.FeedException, e:
        print >>sys.stderr, 'feed exception:', e
        return 1

    print >>sys.stderr, 'connected to', hpc.brokername

    def on_message(identifier, channel, payload):
        procs = PROCESSORS.get(channel, [])
        p = None
        for p in procs:
            try:
                m = p(identifier, payload, gi)
            except Exception, e:
                print "invalid message %s" % payload
                import traceback
                traceback.print_exc(file=sys.stdout)
                continue
            try: tmp = json.dumps(m)
            except: print 'DBG', m
            if m != None: hpc.publish(GEOLOC_CHAN, json.dumps(m))

        if not p:
            print 'not p?'

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
    except:
        import traceback
        traceback.print_exc()
    finally:
        hpc.close()
    return 0

if __name__ == '__main__':
    try: sys.exit(main())
    except KeyboardInterrupt:sys.exit(0)

