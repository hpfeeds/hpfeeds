
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
		req = ezdict(dec.request)
		sip, sport = dec.source
		tstamp = datetime.datetime.strptime(dec.time, '%Y-%m-%d %H:%M:%S')
	except:
		print 'exception processing glastopf event', repr(payload)
		traceback.print_exc()
		return

	if dec.pattern == 'unknown': return None

	a_family = get_addr_family(sip)
	if a_family == socket.AF_INET:
		geoloc = geoloc_none( gi[a_family].record_by_addr(sip) )
	elif a_family == socket.AF_INET6:
		geoloc = geoloc_none( gi[a_family].record_by_addr_v6(sip) )

	return {'type': 'glastopf.events', 'sensor': identifier, 'time': str(tstamp), 'latitude': geoloc['latitude'], 'longitude': geoloc['longitude'], 'source': sip, 'city': geoloc['city'], 'country': geoloc['country_name'], 'countrycode': geoloc['country_code']}


def dionaea_capture(identifier, payload, gi):
	try:
		dec = ezdict(json.loads(str(payload)))
		tstamp = datetime.datetime.now()
	except:
		print 'exception processing dionaea event'
		traceback.print_exc()
		return

	a_family = get_addr_family(dec.saddr)
	if a_family == socket.AF_INET:
		geoloc = geoloc_none( gi[a_family].record_by_addr(dec.saddr) )
		geoloc2 = geoloc_none( gi[a_family].record_by_addr(dec.daddr) )
	elif a_family == socket.AF_INET6:
		geoloc = geoloc_none( gi[a_family].record_by_addr_v6(dec.saddr) )
		geoloc2 = geoloc_none( gi[a_family].record_by_addr_v6(dec.daddr) )

	
	return {'type': 'dionaea.capture', 'sensor': identifier, 'time': timestr(tstamp), 'latitude': geoloc['latitude'], 'longitude': geoloc['longitude'], 'source': dec.saddr, 'latitude2': geoloc2['latitude'], 'longitude2': geoloc2['longitude'], 'dest': dec.daddr, 'md5': dec.md5,
'city': geoloc['city'], 'country': geoloc['country_name'], 'countrycode': geoloc['country_code'],
'city2': geoloc2['city'], 'country2': geoloc2['country_name'], 'countrycode2': geoloc2['country_code']}


def dionaea_connections(identifier, payload, gi):
	try:
		dec = ezdict(json.loads(str(payload)))
		tstamp = datetime.datetime.now()
	except:
		print 'exception processing dionaea event'
		traceback.print_exc()
		return

	a_family = get_addr_family(dec.remote_host)
	if a_family == socket.AF_INET:
		geoloc = geoloc_none( gi[a_family].record_by_addr(dec.remote_host) )
		geoloc2 = geoloc_none( gi[a_family].record_by_addr(dec.local_host) )
	elif a_family == socket.AF_INET6:
		geoloc = geoloc_none( gi[a_family].record_by_addr_v6(dec.remote_host) )
		geoloc2 = geoloc_none( gi[a_family].record_by_addr_v6(dec.local_host) )

	
	return {'type': 'dionaea.connections', 'sensor': identifier, 'time': timestr(tstamp), 'latitude': geoloc['latitude'], 'longitude': geoloc['longitude'], 'source': dec.remote_host, 'latitude2': geoloc2['latitude'], 'longitude2': geoloc2['longitude'], 'dest': dec.local_host, 'md5': dec.md5,
'city': geoloc['city'], 'country': geoloc['country_name'], 'countrycode': geoloc['country_code'],
'city2': geoloc2['city'], 'country2': geoloc2['country_name'], 'countrycode2': geoloc2['country_code']}

def beeswarm_hive(identifier, payload, gi):
	try:
		dec = ezdict(json.loads(str(payload)))
		sip = dec.attacker_ip
		dip = dec.honey_ip
		tstamp = datetime.datetime.strptime(dec.timestamp, '%Y-%m-%dT%H:%M:%S.%f')
	except:
		print 'exception processing beeswarm.hive event', repr(payload)
		traceback.print_exc()
		return

	a_family = get_addr_family(sip)
	if a_family == socket.AF_INET:
		geoloc = geoloc_none( gi[a_family].record_by_addr(sip) )
		geoloc2 = geoloc_none( gi[a_family].record_by_addr(dip) )
	elif a_family == socket.AF_INET6:
		geoloc = geoloc_none( gi[a_family].record_by_addr_v6(sip) )
		geoloc2 = geoloc_none( gi[a_family].record_by_addr_v6(dip) )

	return {'type': 'beeswarm.hive', 'sensor': identifier, 'time': str(tstamp),
            'latitude': geoloc['latitude'], 'longitude': geoloc['longitude'], 'city': geoloc['city'], 'country': geoloc['country_name'], 'countrycode': geoloc['country_code'],
            'latitude2': geoloc2['latitude'], 'longitude2': geoloc2['longitude'], 'city2': geoloc2['city'], 'country2': geoloc2['country_name'], 'countrycode2': geoloc2['country_code']}

def kippo_sessions(identifier, payload, gi):
	try:
		dec = ezdict(json.loads(str(payload)))
		tstamp = datetime.datetime.now()
	except:
		print 'exception processing dionaea event'
		traceback.print_exc()
		return

	a_family = get_addr_family(dec.peerIP)
	if a_family == socket.AF_INET:
		geoloc = geoloc_none( gi[a_family].record_by_addr(dec.peerIP) )
		geoloc2 = geoloc_none( gi[a_family].record_by_addr(dec.hostIP) )
	elif a_family == socket.AF_INET6:
		geoloc = geoloc_none( gi[a_family].record_by_addr_v6(dec.peerIP) )
		geoloc2 = geoloc_none( gi[a_family].record_by_addr_v6(dec.hostIP) )


	return {'type': 'kippo.sessions', 'sensor': identifier, 'time': timestr(tstamp),
'latitude': geoloc['latitude'], 'longitude': geoloc['longitude'], 'source': dec.peerIP,
'latitude2': geoloc2['latitude'], 'longitude2': geoloc2['longitude'], 'dest': dec.hostIP,
'city': geoloc['city'], 'country': geoloc['country_name'], 'countrycode': geoloc['country_code'],
'city2': geoloc2['city'], 'country2': geoloc2['country_name'], 'countrycode2': geoloc2['country_code']}

def conpot_events(identifier, payload, gi):
	try:
		dec = ezdict(json.loads(str(payload)))
		remote = dec.remote[0]

		# http asks locally for snmp with remote ip = "127.0.0.1"
		if remote == "127.0.0.1":
			return

		tstamp = datetime.datetime.strptime(dec.timestamp, '%Y-%m-%dT%H:%M:%S.%f')
	except:
		print 'exception processing conpot event'
		traceback.print_exc()
		return

	a_family = get_addr_family(remote)
	if a_family == socket.AF_INET:
		geoloc = geoloc_none( gi[a_family].record_by_addr(remote) )
		if dec.public_ip:
			geoloc2 = geoloc_none( gi[a_family].record_by_addr(dec.public_ip) )
	elif a_family == socket.AF_INET6:
		geoloc = geoloc_none( gi[a_family].record_by_addr_v6(remote) )
		if dec.public_ip:
			geoloc2 = geoloc_none( gi[a_family].record_by_addr(dec.public_ip) )

	type = 'conpot.events-'+dec.data_type

	message = {'type': type, 'sensor': identifier, 'time': timestr(tstamp),
'latitude': geoloc['latitude'], 'longitude': geoloc['longitude'], 'source': remote,
'city': geoloc['city'], 'country': geoloc['country_name'], 'countrycode': geoloc['country_code']}

	if dec.public_ip:
		message['latitude2'] = geoloc2['latitude']
		message['longitude2'] = geoloc2['longitude']
		message['city2'] = geoloc2['city']
		message['country2'] = geoloc2['country_name']
		message['countrycode2'] = geoloc2['country_code']

	return message

def snort_alerts(identifier, payload, gi):
	# 	{
	#     "classification": "Potentially Bad Traffic",
	#     "date": "2014-05-04T11:49:27.431226",
	#     "destination_ip": "192.241.157.117",
	#     "destination_port": "50649",
	#     "header": "1:2003195:5",
	#     "priority": "2",
	#     "proto": "UDP",
	#     "sensor": "12345",
	#     "signature": "ET POLICY Unusual number of DNS No Such Name Responses",
	#     "source_ip": "8.8.4.4",
	#     "source_port": "53"
	# }

	try:
		dec = ezdict(json.loads(str(payload)))
		tstamp = datetime.datetime.strptime(dec.date, '%Y-%m-%dT%H:%M:%S.%f')
	except:
		print 'exception processing snort alert'
		traceback.print_exc()
		return

	a_family = get_addr_family(dec.source_ip)
	if a_family == socket.AF_INET:
		geoloc = geoloc_none( gi[a_family].record_by_addr(dec.source_ip) )
		if dec.destination_ip:
			geoloc2 = geoloc_none( gi[a_family].record_by_addr(dec.destination_ip) )
	elif a_family == socket.AF_INET6:
		geoloc = geoloc_none( gi[a_family].record_by_addr_v6(dec.source_ip) )
		if dec.destination_ip:
			geoloc2 = geoloc_none( gi[a_family].record_by_addr(dec.destination_ip) )

	message = {
		'type': 'snort.alerts', 
		'sensor': identifier, 
		'time': timestr(tstamp),
		'latitude': geoloc['latitude'], 
		'longitude': geoloc['longitude'], 
		'source': dec.source_ip,
		'city': geoloc['city'], 
		'country': geoloc['country_name'], 
		'countrycode': geoloc['country_code']
	}

	if geoloc2:
		message.update({
			'latitude2': geoloc2['latitude'],
			'longitude2': geoloc2['longitude'],
			'city2': geoloc2['city'],
			'country2': geoloc2['country_name'],
			'countrycode2': geoloc2['country_code']
		})

	return message

def amun_events(identifier, payload, gi):
        try:
                dec = ezdict(json.loads(str(payload)))
                tstamp = datetime.datetime.now()
        except:
                print 'exception processing amun event'
                traceback.print_exc()
                return

        a_family = get_addr_family(dec.attackerIP)
        if a_family == socket.AF_INET:
                geoloc = geoloc_none( gi[a_family].record_by_addr(dec.attackerIP) )
                geoloc2 = geoloc_none( gi[a_family].record_by_addr(dec.victimIP) )
        elif a_family == socket.AF_INET6:
                geoloc = geoloc_none( gi[a_family].record_by_addr_v6(dec.attackerIP) )
                geoloc2 = geoloc_none( gi[a_family].record_by_addr_v6(dec.victimIP) )


        return {'type': 'amun.events', 'sensor': identifier, 'time': timestr(tstamp),
                'latitude': geoloc['latitude'], 'longitude': geoloc['longitude'], 'source': dec.attackerIP,
                'latitude2': geoloc2['latitude'], 'longitude2': geoloc2['longitude'], 'dest': dec.victimIP,
                'city': geoloc['city'], 'country': geoloc['country_name'], 'countrycode': geoloc['country_code'],
                'city2': geoloc2['city'], 'country2': geoloc2['country_name'], 'countrycode2': geoloc2['country_code']}

def wordpot_event(identifier, payload, gi):
	try:
		dec = ezdict(json.loads(str(payload)))
	except:
		print 'exception processing wordpot alert'
		traceback.print_exc()
		return

	a_family = get_addr_family(dec.source_ip)
	if a_family == socket.AF_INET:
		geoloc = geoloc_none( gi[a_family].record_by_addr(dec.source_ip) )
		if dec.dest_ip:
			geoloc2 = geoloc_none( gi[a_family].record_by_addr(dec.dest_ip) )
	elif a_family == socket.AF_INET6:
		geoloc = geoloc_none( gi[a_family].record_by_addr_v6(dec.source_ip) )
		if dec.dest_ip:
			geoloc2 = geoloc_none( gi[a_family].record_by_addr(dec.dest_ip) )

	message = {
		'type': 'wordpot.alerts', 
		'sensor': identifier, 
		'time': timestr(datetime.datetime.now()),
		'latitude': geoloc['latitude'], 
		'longitude': geoloc['longitude'], 
		'source': dec.source_ip,
		'city': geoloc['city'], 
		'country': geoloc['country_name'], 
		'countrycode': geoloc['country_code']
	}

	if geoloc2:
		message.update({
			'latitude2': geoloc2['latitude'],
			'longitude2': geoloc2['longitude'],
			'city2': geoloc2['city'],
			'country2': geoloc2['country_name'],
			'countrycode2': geoloc2['country_code']
		})

	return message

# TODO: use this function everywhere else is can be to clean up this code.
def create_message(event_type, identifier, gi, src_ip, dst_ip):
	a_family = get_addr_family(src_ip)
	if a_family == socket.AF_INET:
		geoloc = geoloc_none( gi[a_family].record_by_addr(src_ip) )
		if dst_ip:
			geoloc2 = geoloc_none( gi[a_family].record_by_addr(dst_ip) )
	elif a_family == socket.AF_INET6:
		geoloc = geoloc_none( gi[a_family].record_by_addr_v6(src_ip) )
		if dst_ip:
			geoloc2 = geoloc_none( gi[a_family].record_by_addr(dst_ip) )

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
