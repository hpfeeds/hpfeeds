
import json
import traceback
import datetime
import urlparse

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

	geoloc = geoloc_none( gi.record_by_addr(sip) )

	return {'type': 'glastopf.events', 'sensor': identifier, 'time': str(tstamp), 'latitude': geoloc['latitude'], 'longitude': geoloc['longitude'], 'source': sip, 'city': geoloc['city'], 'country': geoloc['country_name'], 'countrycode': geoloc['country_code']}


def dionaea_capture(identifier, payload, gi):
	try:
		dec = ezdict(json.loads(str(payload)))
		tstamp = datetime.datetime.now()
	except:
		print 'exception processing dionaea event'
		traceback.print_exc()
		return

	geoloc = geoloc_none( gi.record_by_addr(dec.saddr) )
	geoloc2 = geoloc_none( gi.record_by_addr(dec.daddr) )
	
	return {'type': 'dionaea.capture', 'sensor': identifier, 'time': timestr(tstamp), 'latitude': geoloc['latitude'], 'longitude': geoloc['longitude'], 'source': dec.saddr, 'latitude2': geoloc2['latitude'], 'longitude2': geoloc2['longitude'], 'dest': dec.daddr, 'md5': dec.md5,
'city': geoloc['city'], 'country': geoloc['country_name'], 'countrycode': geoloc['country_code'],
'city2': geoloc2['city'], 'country2': geoloc2['country_name'], 'countrycode2': geoloc2['country_code']}


