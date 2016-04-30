
import json
import traceback
import datetime
import urlparse
import socket

class ezdict(object):
    def __init__(self, d):
        self.d = d
    def __getattr__(self, name):
        return self.d.get(name, None)

# time string
def timestr(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# geoloc_none
def geoloc_none(t):
    if t == None: return {'latitude': None, 'longitude': None, 'city': None, 'country_name': None, 'country_code': None}
    if t['city'] != None: t['city'] = t['city'].decode('latin1')
    return t

def get_addr_family(addr):
        ainfo = socket.getaddrinfo(addr, 1, socket.AF_UNSPEC, socket.SOCK_STREAM)
        return ainfo[0][0]

def glastopf_event(identifier, payload, gi):
    try:
        dec = ezdict(json.loads(str(payload)))
    except:
        print 'exception processing glastopf event'
        traceback.print_exc()
        return

    if dec.pattern == 'unknown': 
        return None

    return create_message('glastopf.events', identifier, gi, src_ip=dec.source[0], dst_ip=None)

def dionaea_capture(identifier, payload, gi):
    try:
        dec = ezdict(json.loads(str(payload)))
    except:
        print 'exception processing dionaea event'
        traceback.print_exc()
        return
    return create_message('dionaea.capture', identifier, gi, src_ip=dec.saddr, dst_ip=dec.daddr)

def dionaea_connections(identifier, payload, gi):
    try:
        dec = ezdict(json.loads(str(payload)))
    except:
        print 'exception processing dionaea connection'
        traceback.print_exc()
        return
    return create_message('dionaea.connections', identifier, gi, src_ip=dec.remote_host, dst_ip=dec.local_host)

def beeswarm_hive(identifier, payload, gi):
    try:
        dec = ezdict(json.loads(str(payload)))
    except:
        print 'exception processing beeswarm.hive event'
        traceback.print_exc()
        return
    return create_message('beeswarm.hive', identifier, gi, src_ip=dec.attacker_ip, dst_ip=dec.honey_ip)

def cowrie_sessions(identifier, payload, gi):
    try:
        dec = ezdict(json.loads(str(payload)))
    except:
        print 'exception processing cowrie event'
        traceback.print_exc()
        return
    return create_message('cowrie.sessions', identifier, gi, src_ip=dec.peerIP, dst_ip=dec.hostIP)

def kippo_sessions(identifier, payload, gi):
    try:
        dec = ezdict(json.loads(str(payload)))
    except:
        print 'exception processing kippo event'
        traceback.print_exc()
        return
    return create_message('kippo.sessions', identifier, gi, src_ip=dec.peerIP, dst_ip=dec.hostIP)

def conpot_events(identifier, payload, gi):
    try:
        dec = ezdict(json.loads(str(payload)))
        remote = dec.remote[0]

        # http asks locally for snmp with remote ip = "127.0.0.1"
        if remote == "127.0.0.1":
            return
    except:
        print 'exception processing conpot event'
        traceback.print_exc()
        return

    return create_message('conpot.events-'+dec.data_type, identifier, gi, src_ip=remote, dst_ip=dec.public_ip)

def snort_alerts(identifier, payload, gi):
    try:
        dec = ezdict(json.loads(str(payload)))
    except:
        print 'exception processing snort alert'
        traceback.print_exc()
        return None
    return create_message('snort.alerts', identifier, gi, src_ip=dec.source_ip, dst_ip=dec.destination_ip)

def suricata_events(identifier, payload, gi):
    try:
        dec = ezdict(json.loads(str(payload)))
    except:
        print 'exception processing suricata event'
        traceback.print_exc()
        return None
    return create_message('suricata.events', identifier, gi, src_ip=dec.source_ip, dst_ip=dec.destination_ip)

def amun_events(identifier, payload, gi):
    try:
        dec = ezdict(json.loads(str(payload)))
    except:
        print 'exception processing amun event'
        traceback.print_exc()
        return
    return create_message('amun.events', identifier, gi, src_ip=dec.attackerIP, dst_ip=dec.victimIP)

def wordpot_event(identifier, payload, gi):
    try:
        dec = ezdict(json.loads(str(payload)))
    except:
        print 'exception processing wordpot alert'
        traceback.print_exc()
        return

    return create_message('wordpot.alerts', identifier, gi, src_ip=dec.source_ip, dst_ip=dec.dest_ip)

# TODO: use this function everywhere else is can be to clean up this code.
def create_message(event_type, identifier, gi, src_ip, dst_ip):
    geoloc = None
    geoloc2 = None
    a_family = get_addr_family(src_ip)
    if a_family == socket.AF_INET:
        geoloc = geoloc_none( gi[a_family].record_by_addr(src_ip) )
        if dst_ip:
            geoloc2 = geoloc_none( gi[a_family].record_by_addr(dst_ip) )
    elif a_family == socket.AF_INET6:
        geoloc = geoloc_none( gi[a_family].record_by_addr_v6(src_ip) )
        if dst_ip:
            geoloc2 = geoloc_none( gi[a_family].record_by_addr_v6(dst_ip) )

    message = {
        'type':   event_type, 
        'sensor': identifier, 
        'time':   timestr(datetime.datetime.now()),
        'source': src_ip,

        'latitude':    geoloc['latitude'], 
        'longitude':   geoloc['longitude'], 
        'city':        geoloc['city'], 
        'country':     geoloc['country_name'], 
        'countrycode': geoloc['country_code']
    }

    if geoloc2:
        message.update({
            'latitude2':    geoloc2['latitude'],
            'longitude2':   geoloc2['longitude'],
            'city2':        geoloc2['city'],
            'country2':     geoloc2['country_name'],
            'countrycode2': geoloc2['country_code']
        })

    return message

def shockpot_event(identifier, payload, gi):
    try:
        dec = ezdict(json.loads(str(payload)))
    except:
        print 'exception processing shockpot alert'
        traceback.print_exc()
        return None

    try:
        p = urlparse.urlparse(dec.url)
        socket.inet_aton(urlparse.urlparse(dec.url).netloc)
        dest_ip = p.netloc
    except:
        dest_ip = None

    return create_message('shockpot.events', identifier, gi, src_ip=dec.source_ip, dst_ip=dest_ip)

def p0f_event(identifier, payload, gi):
    try:
        dec = ezdict(json.loads(str(payload)))
    except:
        print 'exception processing p0f alert'
        traceback.print_exc()
        return None
    return create_message('p0f.events', identifier, gi, src_ip=dec.client_ip, dst_ip=dec.server_ip)

def elastichoney_events(identifier, payload, gi):
    try:
        dec = ezdict(json.loads(str(payload)))
    except:
        print 'exception processing elastichoney event'
        traceback.print_exc()
        return None
    return create_message('elastichoney.events', identifier, gi, src_ip=dec.source, dst_ip=dec.honeypot)
