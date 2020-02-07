import logging
import motor.motor_asyncio

# inserting a user:
# mongo
# db.auth_key.insert({"identifier": "testin", "secret": "secretkey", "publish": ["chan1", "chan2"], subscribe: ["chan2"]})
# Connection string example mongodb://username:password@mongohost:27017/dbname


class Authenticator(object):

    def __init__(self, connection_string):
        self.logger = logging.getLogger('broker.auth.mongo.Authenticator')
        self.logger.info('Creating Authenticator Class')
        try:
            dbstring, dbname = connection_string.rsplit('/', 1)
            self.client = motor.motor_asyncio.AsyncIOMotorClient(dbstring)
            self.db = self.client[dbname]
            self.collection = self.db['auth_key']
        except Exception as err:
            ServerException (hpfeeds.broker.server.ServerException)
            self.logger.error("Error connecting to mongo database: {0}".format(err))

    async def start(self):
        pass

    async def close(self):
        self.logger.debug("Closing Mongo Connection")
        self.client.close()

    async def get_authkey(self, ident):
        self.logger.debug("Auth key for {0} requested".format(ident))
        auth_key = self.collection.find_one({"identifier": ident})

        if not auth_key:
            return None

        return dict(
            owner=auth_key['identifier'],
            secret=auth_key['secret'],
            ident=auth_key['identifier'],
            pubchans=auth_key['publish'],
            subchans=auth_key['subscribe'],
        )
