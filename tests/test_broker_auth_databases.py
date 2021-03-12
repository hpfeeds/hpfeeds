import asyncio
import os
import unittest

from hpfeeds.broker.auth.database import Authenticator


def async_test(coro):
    """" Helper to manage await calls in unittests """
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(coro(*args, **kwargs))
        finally:
            loop.close()
    return wrapper


class TestAuthenticator(unittest.TestCase):
    def setup(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(None)

    @async_test
    async def test_database_sqlite(self):

        a = Authenticator("database+sqlite:////tmp/test.db")

        # Connect to the database
        await a.database.connect()

        # Create the table if the testdb doesnt already exist

        if not os.path.exists("/tmp/test.db"):

            create_query = """
                CREATE TABLE `auth_keys` (
                    `id` int AUTO_INCREMENT NOT NULL ,
                    `identifier` varchar(36) DEFAULT NULL,
                    `secret` varchar(36) DEFAULT NULL,
                    `publish` json DEFAULT NULL,
                    `subscribe` json DEFAULT NULL,
                    PRIMARY KEY (`id`)
                    )"""

            await a.database.execute(query=create_query)

            # Add a user
            write_query = """INSERT INTO auth_keys (id, identifier, secret, publish, subscribe)
                             VALUES (1, 'aaa', 'bbb', '["a", "b", "c"]', '["d", "e", "f"]')"""

            await a.database.execute(query=write_query)

        # Fetch a row
        key = await a.get_authkey("aaa")

        # Validate the results
        assert key["owner"] == 'aaa'
        assert key["secret"] == 'bbb'
        assert key['pubchans'] == ['a', 'b', 'c']
        assert key['subchans'] == ['d', 'e', 'f']
