import asyncio
import logging

import motor.motor_asyncio
from hpfeeds.broker.server import ServerException

# inserting a user:
# mongo
# db.auth_key.insert({"identifier": "testin", "secret": "secretkey", "publish": ["chan1", "chan2"], subscribe: ["chan2"]})
# Connection string example mongodb://username:password@mongohost:27017/dbname


class Authenticator(object):

    def __init__(self, connection_string):
        self.logger = logging.getLogger('hpfeeds.broker.auth.mongo.Authenticator')
        self.connection = False
        try:
            self.dbstring, self.dbname = connection_string.rsplit('/', 1)
        except Exception as err:
            ServerException("Unable to create connection string: {0}".format(err))

    async def db_connect(self):
        try:
            self.logger.debug("Connecting to Mongo DB")
            loop = asyncio.get_event_loop()
            self.client = motor.motor_asyncio.AsyncIOMotorClient(self.dbstring, io_loop=loop)
            self.db = self.client[self.dbname]
            self.collection = self.db['auth_key']
        except Exception as err:
            self.connection = False
            ServerException("Unable to connect to mongo database: {0}".format(err))

    async def start(self):
        pass

    async def close(self):
        self.logger.debug("Closing Mongo Connection")
        self.client.close()

    async def get_authkey(self, ident):
        self.logger.debug("Auth key for {0} requested".format(ident))

        # We need to wait for the asyncio loop to be up
        # So set everything up on the first auth call at which point we should be running.
        if not self.connection:
            await self.db_connect()
            self.connection = True

        auth_key = await self.collection.find_one({"identifier": ident})

        if not auth_key:
            return None

        return dict(
            owner=auth_key['identifier'],
            secret=auth_key['secret'],
            ident=auth_key['identifier'],
            pubchans=auth_key['publish'],
            subchans=auth_key['subscribe'],
        )
