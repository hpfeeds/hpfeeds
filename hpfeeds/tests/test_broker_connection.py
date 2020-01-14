import asyncio
import logging
import unittest
from unittest import mock

from hpfeeds.asyncio import ClientSession
from hpfeeds.broker import prometheus
from hpfeeds.broker.auth.memory import Authenticator
from hpfeeds.broker.connection import Connection
from hpfeeds.broker.server import Server
from hpfeeds.protocol import (
    Unpacker,
    msgauth,
    msgpublish,
    msgsubscribe,
    msgunsubscribe,
    readinfo,
    readpublish,
)


def parse(mock_write):
    unpacker = Unpacker()
    for call in mock_write.call_args_list:
        unpacker.feed(call[0][0])
    results = []
    for msg in unpacker:
        results.append(msg)
    return results


class TestBrokerConnection(unittest.TestCase):

    def setUp(self):
        prometheus.reset()

        authenticator = Authenticator({
            'test': {
                'secret': 'secret',
                'subchans': ['test-chan'],
                'pubchans': ['test-chan'],
                'owner': 'some-owner',
            }
        })

        self.server = Server(authenticator)
        self.server.add_endpoint_legacy('127.0.0.1:20000')

    def make_connection(self):
        transport = mock.Mock()
        transport.get_extra_info.side_effect = lambda name: ('127.0.0.1', 80) if name == 'peername' else None

        connection = Connection(self.server)
        connection.connection_made(transport)

        return connection

    def test_sends_challenge(self):
        c = self.make_connection()
        assert parse(c.transport.write)[0][1][:-4] == b'\x07hpfeeds'

    def test_must_auth(self):
        c = self.make_connection()
        c.data_received(msgpublish('a', 'b', b'c'))

        assert parse(c.transport.write)[0][1][:-4] == b'\x07hpfeeds'
        assert parse(c.transport.write)[1][1] == b'First message was not AUTH'

    def test_auth_failure_wrong_secret(self):
        c = self.make_connection()
        name, rand = readinfo(parse(c.transport.write)[0][1])
        c.data_received(msgauth(rand, 'test', 'secret2'))

        assert parse(c.transport.write)[1][1] == b'Authentication failed for test'

    def test_auth_failure_no_such_ident(self):
        c = self.make_connection()
        name, rand = readinfo(parse(c.transport.write)[0][1])
        c.data_received(msgauth(rand, 'test2', 'secret'))

        assert parse(c.transport.write)[1][1] == b'Authentication failed for test2'

    def test_permission_to_sub(self):
        c = self.make_connection()
        name, rand = readinfo(parse(c.transport.write)[0][1])
        c.data_received(msgauth(rand, 'test', 'secret'))
        c.data_received(msgsubscribe('test', 'test-chan2'))

        assert parse(c.transport.write)[1][1] == b'Authkey not allowed to sub here. ident=test, chan=test-chan2'

    def test_permission_to_pub(self):
        c = self.make_connection()
        name, rand = readinfo(parse(c.transport.write)[0][1])
        c.data_received(msgauth(rand, 'test', 'secret'))
        c.data_received(msgpublish('test', 'test-chan2', b'c'))

        assert parse(c.transport.write)[1][1] == b'Authkey not allowed to pub here. ident=test, chan=test-chan2'

    def test_pub_ident_checked(self):
        c = self.make_connection()
        name, rand = readinfo(parse(c.transport.write)[0][1])
        c.data_received(msgauth(rand, 'test', 'secret'))
        c.data_received(msgpublish('wrong-ident', 'test-chan2', b'c'))

        assert parse(c.transport.write)[1][1] == b'Invalid authkey in message, ident=wrong-ident'

    def test_auth_success(self):
        c = self.make_connection()
        name, rand = readinfo(parse(c.transport.write)[0][1])
        c.data_received(msgauth(rand, 'test', 'secret'))
        c.data_received(msgsubscribe('test', 'test-chan'))
        c.data_received(msgpublish('test', 'test-chan', b'c'))

        assert readpublish(parse(c.transport.write)[1][1]) == (
            'test',
            'test-chan',
            b'c'
        )

    def test_multiple_subscribers(self):
        subscribers = []
        for i in range(5):
            c = self.make_connection()
            name, rand = readinfo(parse(c.transport.write)[0][1])
            c.data_received(msgauth(rand, 'test', 'secret'))
            c.data_received(msgsubscribe('test', 'test-chan'))
            subscribers.append(c)

        c = self.make_connection()
        name, rand = readinfo(parse(c.transport.write)[0][1])
        c.data_received(msgauth(rand, 'test', 'secret'))
        c.data_received(msgpublish('test', 'test-chan', b'c'))

        for c in subscribers:
            msgs = parse(c.transport.write)
            assert readpublish(msgs[1][1]) == (
                'test',
                'test-chan',
                b'c'
            )

    def test_auth_unsubscribe(self):
        c = self.make_connection()
        name, rand = readinfo(parse(c.transport.write)[0][1])
        c.data_received(msgauth(rand, 'test', 'secret'))

        c.data_received(msgsubscribe('test', 'test-chan'))
        c.data_received(msgpublish('test', 'test-chan', b'c'))
        c.data_received(msgunsubscribe('test', 'test-chan'))
        c.data_received(msgpublish('test', 'test-chan', b'c'))
        c.data_received(msgsubscribe('test', 'test-chan'))
        c.data_received(msgpublish('test', 'test-chan', b'c'))

        messages = parse(c.transport.write)
        for msg in messages[1:]:
            assert readpublish(msg[1]) == (
                'test',
                'test-chan',
                b'c'
            )

        # 1 auth and 2 publish
        assert len(messages) == 3


class TestBrokerIntegration(unittest.TestCase):

    log = logging.getLogger('hpfeeds.test_broker_connection')

    def setUp(self):
        authenticator = Authenticator({
            'test': {
                'secret': 'secret',
                'subchans': ['test-chan'],
                'pubchans': ['test-chan'],
                'owner': 'some-owner',
            }
        })

        self.server = Server(authenticator)
        self.server.add_endpoint_str("tls:interface=127.0.0.1:port=0:cert=hpfeeds/tests/testcert.crt:key=hpfeeds/tests/testcert.key")

    def test_subscribe_and_publish(self):
        prometheus.reset()

        async def inner():
            self.log.debug('Starting server')
            server_future = asyncio.ensure_future(self.server.serve_forever())
            await self.server.when_started

            self.port = self.server.endpoints[0]['port']

            import ssl
            ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile='hpfeeds/tests/testcert.crt')
            ssl_context.check_hostname = False

            self.log.debug('Creating client service')
            client = ClientSession('127.0.0.1', self.port, 'test', 'secret', ssl=ssl_context)
            client.subscribe('test-chan')

            # Wait till client connected
            await client.when_connected

            assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_client_connections') == 1
            assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_connection_made') == 1

            self.log.debug('Publishing test message')
            client.publish('test-chan', b'test message')

            self.log.debug('Waiting for read()')
            assert ('test', 'test-chan', b'test message') == await client.read()

            # We would test this after call to subscribe, but need to wait until sure server has processed command
            assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_subscriptions', {'ident': 'test', 'chan': 'test-chan'}) == 1

            # This will only have incremented when server has processed auth message
            # Test can only reliably assert this is the case after reading a message
            assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_connection_ready', {'ident': 'test'}) == 1

            self.log.debug('Stopping client')
            await client.close()

            assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_connection_send_buffer_fill', {'ident': 'test'}) == 12
            assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_connection_send_buffer_drain', {'ident': 'test'}) == 32

            self.log.debug('Stopping server')
            server_future.cancel()
            await server_future

        asyncio.get_event_loop().run_until_complete(inner())
        assert len(self.server.connections) == 0, 'Connection left dangling'
        assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_client_connections') == 0
        assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_connection_lost', {'ident': 'test'}) == 1

        # Closing should auto unsubscribe
        assert prometheus.REGISTRY.get_sample_value('hpfeeds_broker_subscriptions', {'ident': 'test', 'chan': 'test-chan'}) == 0
