#!/usr/bin/python
# -*- coding: utf8 -*-

import logging
import os

from hpfeeds.asyncio.protocol import BaseProtocol
from hpfeeds.protocol import OP_AUTH, hashsecret

from .prometheus import CLIENT_CONNECTIONS

log = logging.getLogger('hpfeeds.broker.connection')


class Connection(BaseProtocol):

    def __init__(self, server):
        self.server = server

        self.uid = None
        self.ak = None
        self.pubchans = []
        self.subchans = []

        self.active_subscriptions = set()

        self.authrand = os.urandom(4)

        super().__init__()

    def connection_made(self, transport):
        print("connection_made 1")
        CLIENT_CONNECTIONS.inc()

        self.server.connections.add(self)
        print("connection_made 1")

        self.transport = transport
        self.peer, self.port = transport.get_extra_info('peername')

        print("connection_made 1")

        self.info(self.server.name, self.authrand)

        log.debug(f'{self}: Sent auth challenge')

    def connection_lost(self, reason):
        CLIENT_CONNECTIONS.dec()

        for chan in list(self.active_subscriptions):
            self.server.unsubscribe(self, chan)

        self.server.connections.discard(self)
        self.server = None

        log.debug(f'Disconnection from {self}; cleanup completed.')

    def __str__(self):
        peer, port = self.peer, self.port
        ident = self.ak
        owner = self.uid
        return (
            f'<Connection ident={ident} owner={owner} peer={peer} port={port}'
        )

    def message_received(self, opcode, message):
        if not self.uid and opcode != OP_AUTH:
            self.error("First message was not AUTH")
            self.transport.close()
            return

        return super().message_received(opcode, message)

    def on_auth(self, ident, secret):
        akrow = self.server.get_authkey(ident)
        if not akrow:
            self.error(f"Authentication failed for {ident}")
            self.transport.close()
            return

        print(akrow)
        print(type(akrow))

        akhash = hashsecret(self.authrand, akrow["secret"])
        if not akhash == secret:
            self.error(f"Authentication failed for {ident}")
            self.transport.close()
            return

        self.ak = ident
        self.uid = akrow["owner"]
        self.pubchans = akrow.get("pubchans", [])
        self.subchans = akrow.get("subchans", [])

    def on_publish(self, ident, chan, payload):
        if not ident == self.ak:
            self.error(f"Invalid authkey in message, ident={ident}")
            self.transport.close()
            return

        if chan not in self.pubchans:
            self.error(f'Authkey not allowed to pub here. ident={ident}, chan={chan}')
            self.transport.close()
            return

        self.server.publish(self, chan, payload)

    def on_subscribe(self, ident, chan):
        if chan not in self.subchans:
            self.error(f'Authkey not allowed to sub here. ident={self.ak}, chan={chan}')
            self.transport.close()
        self.server.subscribe(self, chan)

    def on_unsubscribe(self, ident, chan):
        self.server.unsubscribe(self, chan)
