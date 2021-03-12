import json
import logging

from hpfeeds.broker.server import ServerException

try:
    from databases import Database
    lib_databases = True
except ImportError:
    lib_databases = False


class Authenticator(object):

    def __init__(self, connection_string):
        self.logger = logging.getLogger('hpfeeds.broker.auth.databases.Authenticator')
        self.connection_string = connection_string.replace("database+", "")
        self.database = Database(self.connection_string)

        if not lib_databases:
            raise ServerException("The module 'databases.Database' is not available - is the databases package installed?")

    async def db_connect(self):

        try:
            self.logger.debug("Connecting to database")
            await self.database.connect()
        except Exception as err:
            raise Exception(f"Unable to connect to database: {err}")

    async def start(self):
        pass

    async def close(self):
        await self.database.disconnect()

    async def get_authkey(self, ident):
        self.logger.debug(f"Auth key for {ident} requested")

        if not self.database.is_connected:
            await self.db_connect()

        query = "SELECT * from auth_keys WHERE identifier = :ident LIMIT 1"
        result = await self.database.fetch_one(query=query, values={"ident": ident})

        if not result:
            return None

        try:
            auth_key = dict(
                owner=result[1],
                secret=result[2],
                ident=result[1],
                pubchans=json.loads(result[3]),
                subchans=json.loads(result[4]),
            )
        except Exception as err:
            raise Exception(f"Unable to parse auth row from database query: {err}")

        return auth_key
