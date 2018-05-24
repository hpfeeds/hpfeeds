import asyncio
import logging
import socket
import unittest

from hpfeeds.asyncio import Client
from hpfeeds.broker.auth.memory import Authenticator
from hpfeeds.broker.server import Server


class TestAsyncioClientIntegration(unittest.TestCase):

    log = logging.getLogger('hpfeeds.test_asyncio_client')

    def setUp(self):
        self.sock = sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('127.0.0.1', 0))
        self.port = sock.getsockname()[1]

        authenticator = Authenticator({
            'test': {
                'secret': 'secret',
                'subchans': ['test-chan'],
                'pubchans': ['test-chan'],
                'owner': 'some-owner',
            }
        })

        self.server = Server(authenticator, sock=self.sock)

    def test_subscribe_and_publish(self):
        async def inner():
            self.log.debug('Starting server')
            server_future = asyncio.ensure_future(self.server.serve_forever())

            self.log.debug('Creating client service')
            client = Client('127.0.0.1', self.port, 'test', 'secret')
            client.subscribe('test-chan')

            # Wait till client connected
            await client.when_connected

            self.log.debug('Publishing test message')
            client.publish('test-chan', b'test message')

            self.log.debug('Waiting for read()')
            assert ('test', 'test-chan', b'test message') == await client.read()

            self.log.debug('Stopping client')
            client.close()

            self.log.debug('Stopping server')
            server_future.cancel()
            await server_future

        asyncio.get_event_loop().run_until_complete(inner())
        assert len(self.server.connections) == 0, 'Connection left dangling'

    def test_late_subscribe_and_publish(self):
        async def inner():
            self.log.debug('Starting server')
            server_future = asyncio.ensure_future(self.server.serve_forever())

            self.log.debug('Creating client service')
            client = Client('127.0.0.1', self.port, 'test', 'secret')

            # Wait till client connected
            await client.when_connected

            # Subscribe to a new thing after connection is up
            client.subscribe('test-chan')

            self.log.debug('Publishing test message')
            client.publish('test-chan', b'test message')

            self.log.debug('Waiting for read()')
            assert ('test', 'test-chan', b'test message') == await client.read()

            # Unsubscribe while the connection is up
            client.unsubscribe('test-chan')

            # FIXME: How to test that did anything!

            self.log.debug('Stopping client')
            client.close()

            self.log.debug('Stopping server')
            server_future.cancel()
            await server_future

        asyncio.get_event_loop().run_until_complete(inner())
        assert len(self.server.connections) == 0, 'Connection left dangling'
