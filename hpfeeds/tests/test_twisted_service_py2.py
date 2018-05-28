import logging
import unittest

from twisted.internet import defer

from hpfeeds.twisted import ClientSessionService

from .fakebroker import FakeBroker, setup_default_reactor


class TestClientIntegration(unittest.TestCase):

    log = logging.getLogger('hpfeeds.testserver')

    def setUp(self):
        self.reactor = setup_default_reactor(self)

        self.server = FakeBroker()
        self.server.start()

    def test_subscribe_and_publish(self):
        @defer.inlineCallbacks
        def inner(reactor):
            self.log.debug('Creating client service')
            client = ClientSessionService(f'tcp:127.0.0.1:{self.server.port}', 'test', 'secret')
            client.subscribe('test-chan')

            self.log.debug('Starting client service')
            client.startService()

            # Wait till client connected
            self.log.debug('Waiting to be connected')
            yield client.whenConnected

            self.log.debug('Publishing test message')
            client.publish('test-chan', b'test message')

            self.log.debug('Waiting for read()')
            payload = yield client.read()
            assert ('test', 'test-chan', b'test message') == payload

            self.log.debug('Stopping client')
            yield client.stopService()

            self.log.debug('Stopping server for reals')
            yield self.server.close()

        inner(self.reactor).addBoth(lambda *x: print(x)).addBoth(lambda *x: self.reactor.stop())
        self.reactor.run()
