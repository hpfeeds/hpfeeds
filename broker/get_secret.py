import pymongo
import sys

ident = sys.argv[1]
client = pymongo.MongoClient()
results = client.hpfeeds.auth_key.find({'identifier': ident})
if results.count() > 0:
    print results[0]['secret']
