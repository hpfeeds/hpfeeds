import asyncio
import logging
import socket
import unittest

from twisted.internet import asyncioreactor

from hpfeeds.broker import prometheus
from hpfeeds.broker.auth.memory import Authenticator
from hpfeeds.broker.server import Server
from hpfeeds.twisted import ClientSessionService


class TestClientIntegration(unittest.TestCase):

    log = logging.getLogger('hpfeeds.testserver')

    @classmethod
    def setUpClass(cls):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        asyncioreactor.install(eventloop=loop)
        cls.loop = asyncio.get_event_loop()

    def setUp(self):
        prometheus.reset()

        assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_client_connections') == 0
        assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_connection_made') == 0
        assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_connection_ready', {'ident': 'test'}) is None

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
            client = ClientSessionService(f'tcp:127.0.0.1:{self.port}', 'test', 'secret')
            client.subscribe('test-chan')
            client.startService()

            # Wait till client connected
            await client.whenConnected.asFuture(self.loop)

            assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_client_connections') == 1
            assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_connection_made') == 1

            self.log.debug('Publishing test message')
            client.publish('test-chan', b'test message')

            self.log.debug('Waiting for read()')
            assert ('test', 'test-chan', b'test message') == await client.read().asFuture(self.loop)

            # We would test this after call to subscribe, but need to wait until sure server has processed command
            assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_subscriptions', {'ident': 'test', 'chan': 'test-chan'}) == 1

            # This will only have incremented when server has processed auth message
            # Test can only reliably assert this is the case after reading a message
            assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_connection_ready', {'ident': 'test'}) == 1

            self.log.debug('Stopping client')
            await client.stopService().asFuture(self.loop)

            self.log.debug('Stopping server')
            server_future.cancel()
            await server_future

        self.loop.run_until_complete(inner())
        assert len(self.server.connections) == 0, 'Connection left dangling'
        assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_client_connections') == 0
        assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_connection_lost', {'ident': 'test'}) == 1

        # Closing should auto unsubscribe
        assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_subscriptions', {'ident': 'test', 'chan': 'test-chan'}) == 0

    def test_late_subscribe_and_publish(self):
        async def inner():
            self.log.debug('Starting server')
            server_future = asyncio.ensure_future(self.server.serve_forever())

            self.log.debug('Creating client service')
            client = ClientSessionService(f'tcp:127.0.0.1:{self.port}', 'test', 'secret')
            client.startService()

            # Wait till client connected
            await client.whenConnected.asFuture(self.loop)

            assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_client_connections') == 1
            assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_connection_made') == 1

            # Subscribe to a new thing after connection is up
            client.subscribe('test-chan')

            self.log.debug('Publishing test message')
            client.publish('test-chan', b'test message')

            self.log.debug('Waiting for read()')
            assert ('test', 'test-chan', b'test message') == await client.read().asFuture(self.loop)

            # We would test this after call to subscribe, but need to wait until sure server has processed command
            assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_subscriptions', {'ident': 'test', 'chan': 'test-chan'}) == 1

            # Unsubscribe while the connection is up
            client.unsubscribe('test-chan')

            # This will only have incremented when server has processed auth message
            # Test can only reliably assert this is the case after reading a message
            assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_connection_ready', {'ident': 'test'}) == 1

            self.log.debug('Stopping client')
            await client.stopService().asFuture(self.loop)

            self.log.debug('Stopping server')
            server_future.cancel()
            await server_future

        self.loop.run_until_complete(inner())
        assert len(self.server.connections) == 0, 'Connection left dangling'
        assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_client_connections') == 0
        assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_connection_lost', {'ident': 'test'}) == 1

        # Again, we should test this directly after calling unsubscribe(), but no ability to wait
        assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_subscriptions', {'ident': 'test', 'chan': 'test-chan'}) == 0
