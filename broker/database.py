#!/usr/bin/python

import json
import pymongo

import config

class Database(object):
    def __init__(self):
        self.mongo = pymongo.MongoClient()
        self.check_db()

    def check_db(self):
        with self.mongo:
            try:
                res = self.mongo.hpfeeds.auth_key.find()
            except:
                print "setting up collections..."
                res = self.mongo.hpfeeds.auth_key.update({"identifier": 'admin'},{"secret": ''},{"publish": ''},{"subscribe": ''}, upsert=True)
                self.mongo.fsync()

    def log(self, row):
        enc = json.dumps(row)
        with self.mongo:
            db = self.mongo.hpfeeds
            res = db.logs.insert({"data": enc})

    def close(self):
        self.mongo.disconnect()

    def get_authkey(self, ident):
        with self.mongo:
            try:
                res = self.mongo.hpfeeds.auth_key.find_one({"identifier":ident})
            except:
                import traceback
                traceback.print_exec()
                return NONE
            finally:
                self.mongo.close()
