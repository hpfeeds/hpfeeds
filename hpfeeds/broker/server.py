#!/usr/bin/python
# -*- coding: utf8 -*-

import asyncio
import collections
import logging

from hpfeeds.exceptions import BadClient, Disconnect

from .connection import Connection
from .prometheus import (
    CLIENT_CONNECTIONS,
    RECEIVE_PUBLISH_COUNT,
    RECEIVE_PUBLISH_SIZE,
    SUBSCRIPTIONS,
    start_metrics_server,
)

log = logging.getLogger("hpfeeds.broker")


class Server(object):

    def __init__(self, auth, bind=None, exporter=None, sock=None, ssl=None, name='hpfeeds'):
        self.auth = auth
        self.name = name

        self.host, self.port = self._parse_endpoint(bind)
        self.sock = sock
        self.ssl = ssl

        self.exporter = self._parse_endpoint(exporter)

        self.connections = set()
        self.subscriptions = collections.defaultdict(list)

    def _parse_endpoint(self, endpoint):
        if not endpoint:
            return (None, None)
        elif ':' not in endpoint:
            raise ValueError('Invalid bind addr')
        else:
            return endpoint.split(':', 1)

    async def _handle_connection(self, reader, writer):
        '''
        This is called for each connection to our bound address/port to setup a
        new Connection object and handle lifecycle management.
        '''

        connection = Connection(self, reader, writer)
        self.connections.add(connection)

        log.debug(f'Connection from {connection}.')

        try:
            with CLIENT_CONNECTIONS.track_inprogress():
                try:
                    await connection.handle()
                except Disconnect:
                    log.debug(f'Connection closed by {connection}')
                except BadClient:
                    log.warn(f'Connection ended; bad client: {connection}')
        finally:
            for chan in list(connection.active_subscriptions):
                await self.unsubscribe(connection, chan)

            if connection in self.connections:
                self.connections.remove(connection)

            log.debug(f'Disconnection from {connection}; cleanup completed.')

    def get_authkey(self, identifier):
        return self.auth.get_authkey(identifier)

    async def publish(self, source, chan, data):
        '''
        Called by a connection to push data to all subscribers of a channel
        '''
        RECEIVE_PUBLISH_COUNT.labels(source.ak, chan).inc()
        RECEIVE_PUBLISH_SIZE.labels(source.ak, chan).observe(len(data))

        for dest in self.subscriptions[chan]:
            await dest.publish(source.ak, chan, data)

    async def subscribe(self, source, chan):
        '''
        Subscribe a connection to a channel
        '''
        SUBSCRIPTIONS.labels(source.ak, chan).inc()
        self.subscriptions[chan].append(source)
        source.active_subscriptions.add(chan)

    async def unsubscribe(self, source, chan):
        '''
        Unsubscribe a connection from a channel
        '''
        if chan in source.active_subscriptions:
            source.active_subscriptions.remove(chan)
        if source in self.subscriptions[chan]:
            self.subscriptions[chan].remove(source)
        SUBSCRIPTIONS.labels(source.ak, chan).dec()

    async def serve_forever(self):
        ''' Start handling connections. Await on this to listen forever. '''

        if self.exporter:
            metrics_server = await start_metrics_server(*self.exporter)

        server = await asyncio.start_server(
            self._handle_connection,
            host=self.host,
            port=self.port,
            sock=self.sock,
            ssl=self.ssl,
        )

        try:
            while True:
                await asyncio.sleep(10)
        except asyncio.CancelledError:
            server.close()

            for future in asyncio.as_completed([c.close() for c in list(self.connections)]):
                try:
                    await future
                except Exception as e:
                    log.exception(e)

            log.debug(f'Waiting for {self} to wrap up')
            await server.wait_closed()

            if self.exporter:
                log.debug('Waiting for stats server to wrap up')
                await metrics_server.cleanup()
