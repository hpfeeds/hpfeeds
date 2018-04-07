import asyncio
import unittest

import aiomock

from hpfeeds.broker.connection import Connection
from hpfeeds.protocol import msgpublish


class TestConnection(unittest.TestCase):

    def setUp(self):
        self.server = aiomock.AIOMock()
        self.server.name = 'hpfeeds'

        self.reader = aiomock.AIOMock()
        self.writer = aiomock.AIOMock()
        self.writer.get_extra_info.return_value = ('127.0.0.1', 65432)
        self.writer.drain.async_return_value = None

        self.connection = Connection(self.server, self.reader, self.writer)

    def test_sends_challenge(self):
        asyncio.get_event_loop().run_until_complete(self.connection.handle())
        assert self.writer.write.call_args[0][0][:-4] == b'\x00\x00\x00\x11\x01\x07hpfeeds'

    def test_must_auth(self):
        test_message = msgpublish('a', 'b', b'c')
        self.reader.read.async_return_value = test_message
        asyncio.get_event_loop().run_until_complete(self.connection.handle())
        assert self.writer.write.call_args_list[-1][0][0] == b'\x00\x00\x00\x1f\x00First message was not AUTH'
