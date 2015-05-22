#!/usr/bin/python

import pymongo
import sys

client = pymongo.MongoClient()
for doc in client.hpfeeds.auth_key.find():
    print doc


