import asyncio
import unittest

from hpfeeds.broker.auth.memory import Authenticator
from hpfeeds.broker.connection import HpfeedsReader
from hpfeeds.broker.server import Server
from hpfeeds.protocol import (
    msgauth,
    msgpublish,
    msgsubscribe,
    msgunsubscribe,
    readerror,
    readinfo,
    readpublish,
)


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
            try:
                self.buffer = await asyncio.wait_for(self.queue.get(), 1)
            except asyncio.TimeoutError:
                return b''

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

        self.server = Server(authenticator, bind='127.0.0.1:20000')

        self.client_reader, self.server_writer = setup_pipe()
        self.server_reader, self.client_writer = setup_pipe()

        self.client_reader = HpfeedsReader(self.client_reader)

    def make_connection(self):
        client_reader, server_writer = setup_pipe()
        server_reader, client_writer = setup_pipe()

        client_reader = HpfeedsReader(client_reader)

        connection = asyncio.ensure_future(
            self.server._handle_connection(server_reader, server_writer)
        )

        return connection, client_reader, client_writer

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

    def test_auth_failure_wrong_secret(self):
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

            # Should be an error
            op, data = await self.client_reader.read_message()
            assert op == 0
            assert readerror(data) == 'Authentication failed for test'

        asyncio.get_event_loop().run_until_complete(inner())

    def test_auth_failure_no_such_ident(self):
        async def inner():
            connection = asyncio.ensure_future(
                self.server._handle_connection(self.server_reader, self.server_writer)
            )

            op, data = await self.client_reader.read_message()
            assert op == 1
            name, rand = readinfo(data)

            self.client_writer.write(msgauth(rand, 'test2', 'secret'))
            self.client_writer.write(b'')

            await connection

            # Should be an error
            op, data = await self.client_reader.read_message()
            assert op == 0
            assert readerror(data) == 'Authentication failed for test2'

        asyncio.get_event_loop().run_until_complete(inner())

    def test_permission_to_sub(self):
        async def inner():
            connection = asyncio.ensure_future(
                self.server._handle_connection(self.server_reader, self.server_writer)
            )

            op, data = await self.client_reader.read_message()
            assert op == 1
            name, rand = readinfo(data)

            self.client_writer.write(msgauth(rand, 'test', 'secret'))
            self.client_writer.write(msgsubscribe('test', 'test-chan-2'))

            # Should be an error
            op, data = await self.client_reader.read_message()
            assert op == 0
            assert readerror(data) == 'Authkey not allowed to sub here. ident=test, chan=test-chan-2'

            self.client_writer.write(b'')
            await connection

        asyncio.get_event_loop().run_until_complete(inner())

    def test_permission_to_pub(self):
        async def inner():
            connection = asyncio.ensure_future(
                self.server._handle_connection(self.server_reader, self.server_writer)
            )

            op, data = await self.client_reader.read_message()
            assert op == 1
            name, rand = readinfo(data)

            self.client_writer.write(msgauth(rand, 'test', 'secret'))
            self.client_writer.write(msgsubscribe('test', 'test-chan'))
            self.client_writer.write(msgpublish('test', 'test-chan-2', b'c'))

            # Should be an error
            op, data = await self.client_reader.read_message()
            assert op == 0
            assert readerror(data) == 'Authkey not allowed to pub here. ident=test, chan=test-chan-2'

            self.client_writer.write(b'')
            await connection

        asyncio.get_event_loop().run_until_complete(inner())

    def test_pub_ident_checked(self):
        async def inner():
            connection = asyncio.ensure_future(
                self.server._handle_connection(self.server_reader, self.server_writer)
            )

            op, data = await self.client_reader.read_message()
            assert op == 1
            name, rand = readinfo(data)

            self.client_writer.write(msgauth(rand, 'test', 'secret'))
            self.client_writer.write(msgpublish('wrong-ident', 'test-chan', b'c'))

            # Should be an error
            op, data = await self.client_reader.read_message()
            assert op == 0
            assert readerror(data) == 'Invalid authkey in message, ident=wrong-ident'

            self.client_writer.write(b'')
            await connection

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

    def test_multiple_subscribers(self):
        async def inner():
            # Start 5 connections that subscribe to test-chan
            subscribers = []
            for i in range(5):
                conn, reader, writer = self.make_connection()

                op, data = await reader.read_message()
                assert op == 1
                name, rand = readinfo(data)

                writer.write(msgauth(rand, 'test', 'secret'))
                writer.write(msgsubscribe('test', 'test-chan'))
                subscribers.append((conn, reader, writer))

            connection = asyncio.ensure_future(
                self.server._handle_connection(self.server_reader, self.server_writer)
            )

            op, data = await self.client_reader.read_message()
            assert op == 1
            name, rand = readinfo(data)

            self.client_writer.write(msgauth(rand, 'test', 'secret'))
            self.client_writer.write(msgpublish('test', 'test-chan', b'c'))
            self.client_writer.write(b'')

            await connection

            for conn, reader, writer in subscribers:
                op, data = await reader.read_message()
                assert op == 3
                assert readpublish(data) == (
                    'test',
                    'test-chan',
                    b'c'
                )
                writer.write(b'')
                await conn

        asyncio.get_event_loop().run_until_complete(inner())

    def test_auth_unsubscribe(self):
        async def inner():
            connection = asyncio.ensure_future(
                self.server._handle_connection(self.server_reader, self.server_writer)
            )

            op, data = await self.client_reader.read_message()
            assert op == 1
            name, rand = readinfo(data)

            self.client_writer.write(msgauth(rand, 'test', 'secret'))
            self.client_writer.write(msgsubscribe('test', 'test-chan'))
            self.client_writer.write(msgpublish('test', 'test-chan', b'1'))
            self.client_writer.write(msgunsubscribe('test', 'test-chan'))
            self.client_writer.write(msgpublish('test', 'test-chan', b'2'))
            self.client_writer.write(msgsubscribe('test', 'test-chan'))
            self.client_writer.write(msgpublish('test', 'test-chan', b'3'))
            self.client_writer.write(b'')

            await connection

            # The middle publish event should be missing
            op, data = await self.client_reader.read_message()
            assert op == 3
            assert readpublish(data) == (
                'test',
                'test-chan',
                b'1'
            )

            op, data = await self.client_reader.read_message()
            assert op == 3
            assert readpublish(data) == (
                'test',
                'test-chan',
                b'3'
            )

        asyncio.get_event_loop().run_until_complete(inner())
