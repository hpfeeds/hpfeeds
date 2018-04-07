import asyncio
import unittest

from hpfeeds.broker.auth.memory import Authenticator
from hpfeeds.broker.connection import HpfeedsReader
from hpfeeds.broker.server import Server
from hpfeeds.protocol import msgauth, msgpublish, msgsubscribe, readerror, readinfo, readpublish


class QueueWriter(object):

    def __init__(self, queue):
        self.queue = queue

    def get_extra_info(self, key):
        return ('127.0.0.1', 8080)

    def write(self, data):
        print(self, 'write', data)
        self.queue.put_nowait(data)

    async def drain(self):
        pass

    def close(self):
        pass


class QueueReader(object):

    def __init__(self, queue):
        self.queue = queue
        self.buffer = b''

    async def read(self, amt):
        if not self.buffer:
            self.buffer = await self.queue.get()

        buffer, self.buffer = self.buffer[:amt], self.buffer[amt:]

        print(self, 'read', amt, buffer)

        return buffer

    def close(self):
        pass


def setup_pipe():
    queue = asyncio.Queue()
    reader = QueueReader(queue)
    writer = QueueWriter(queue)
    return reader, writer


class TestBrokerIntegration(unittest.TestCase):

    def setUp(self):
        authenticator = Authenticator({
            'test': {
                'secret': 'secret',
                'subchans': ['test-chan'],
                'pubchans': ['test-chan'],
                'owner': 'some-owner',
            }
        })

        self.server = Server(authenticator, address='127.0.0.1', port=20000)

        self.client_reader, self.server_writer = setup_pipe()
        self.server_reader, self.client_writer = setup_pipe()

        self.client_reader = HpfeedsReader(self.client_reader)

    def test_sends_challenge(self):
        async def inner():
            self.client_writer.write(b'')
            await self.server._handle_connection(self.server_reader, self.server_writer)
            data = await self.client_reader.read_message()
            assert data[1][:-4] == b'\x07hpfeeds'
        asyncio.get_event_loop().run_until_complete(inner())

    def test_must_auth(self):
        async def inner():
            test_message = msgpublish('a', 'b', b'c')
            self.client_writer.write(test_message)
            self.client_writer.write(b'')

            await self.server._handle_connection(self.server_reader, self.server_writer)

            # Ignore challenge
            op, data = await self.client_reader.read_message()
            assert op == 1

            # Should be an error message
            op, data = await self.client_reader.read_message()
            assert op == 0
            assert data == b'First message was not AUTH'

        asyncio.get_event_loop().run_until_complete(inner())

    def test_auth_failure(self):
        async def inner():
            connection = asyncio.ensure_future(
                self.server._handle_connection(self.server_reader, self.server_writer)
            )

            op, data = await self.client_reader.read_message()
            assert op == 1
            name, rand = readinfo(data)

            self.client_writer.write(msgauth(rand, 'test', 'secret2'))
            self.client_writer.write(b'')

            await connection

            # Should be a publish event
            op, data = await self.client_reader.read_message()
            assert op == 0
            assert readerror(data) == 'Authentication failed for test'

        asyncio.get_event_loop().run_until_complete(inner())

    def test_auth_success(self):
        async def inner():
            connection = asyncio.ensure_future(
                self.server._handle_connection(self.server_reader, self.server_writer)
            )

            op, data = await self.client_reader.read_message()
            assert op == 1
            name, rand = readinfo(data)

            self.client_writer.write(msgauth(rand, 'test', 'secret'))
            self.client_writer.write(msgsubscribe('test', 'test-chan'))
            self.client_writer.write(msgpublish('test', 'test-chan', b'c'))
            self.client_writer.write(b'')

            await connection

            # Should be a publish event
            op, data = await self.client_reader.read_message()
            assert op == 3
            assert readpublish(data) == (
                'test',
                'test-chan',
                b'c'
            )

        asyncio.get_event_loop().run_until_complete(inner())
