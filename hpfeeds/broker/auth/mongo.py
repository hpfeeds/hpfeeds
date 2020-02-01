import json
import pymongo
from pymongo import MongoClient

# inserting a user:
# mongo
# db.auth_key.insert({"identifier": "testin", "secret": "secretkey", "publish": ["chan1", "chan2"], subscribe: ["chan2"]})

# Connection string example mongodb://username:password@mongohost:27017/dbname


class Authenticator(object):

    def __init__(self, connection_string):
        self.client = MongoClient(connection_string)

    async def start(self):
        pass

    def close(self):
        self.client.close()

    def get_authkey(self, ident):

        auth_collection = self.client['auth_key']

        auth_key = auth_collection.find_one({"identifier", ident})

        if not auth_key:
            return None

        return dict(
            secret=auth_key['secret'],
            ident=auth_key['identifier'],
            pubchans=auth_key['publish'],
            subchans=auth_key['subscribe'],
        )
