#!/usr/bin/python

import pymongo
import sys

def handle_list(arg):
    if arg:
        return arg.split(",")
    else:
        return []

if len(sys.argv) < 2:
    print >> sys.stderr, "Usage: %s <ident>"%sys.argv[0]
    sys.exit(1)

ident = sys.argv[1]

client = pymongo.MongoClient()
res = client.hpfeeds.auth_key.remove({"identifier": ident})
client.fsync()
client.close()


if res['ok']:
    if res['n'] > 0:
        print "deleted user %s"%ident
    else:
        print "user %s does not exist"%ident
else:
    print "failed to delete user %s"%ident
