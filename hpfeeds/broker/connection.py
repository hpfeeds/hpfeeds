#!/usr/bin/python
# -*- coding: utf8 -*-

import asyncio
import os
import logging

from hpfeeds.exceptions import BadClient, Disconnect
from hpfeeds.protocol import (
    BUFSIZ,
    OP_AUTH,
    OP_SUBSCRIBE,
    OP_UNSUBSCRIBE,
    OP_PUBLISH,
    msgerror,
    msginfo,
    msgpublish,
    readsubscribe,
    readpublish,
    readauth,
    hashsecret,
    Unpacker,
)


log = logging.getLogger('hpfeeds.connection')


class HpfeedsReader(object):

    def __init__(self, reader):
        self.reader = reader
        self.unpacker = Unpacker()

    async def read_message(self):
        while not self.unpacker.ready():
            data = await self.reader.read(BUFSIZ)
            if not data:
                raise Disconnect('Reader has disconnected')
            self.unpacker.feed(data)

        return self.unpacker.pop()


class Connection(object):

    def __init__(self, server, reader, writer):
        self.server = server
        self.reader = HpfeedsReader(reader)
        self.writer = writer

        self.active_subscriptions = set()

        self.uid = None
        self.ak = None
        self.pubchans = []
        self.subchans = []
        self.active = True
        self.send_queue = asyncio.Queue()
        self.unpacker = Unpacker()
        self.authrand = os.urandom(4)

    def __str__(self):
        peer, port = self.writer.get_extra_info('peername')
        ident = self.ak
        owner = self.uid
        return (
            f'<Connection ident={ident} owner={owner} peer={peer} port={port}'
        )

    async def write(self, message):
        if self.active:
            await self.send_queue.put(message)

    async def publish(self, ident, chan, payload):
        await self.write(msgpublish(ident, chan, payload))

    async def error(self, error):
        await self.write(msgerror(error))

    async def _process_send_queue(self):
        while self.active or not self.send_queue.empty():
            try:
                payload = await self.send_queue.get()
                self.writer.write(payload)
            except Exception as e:
                self.active = False
                self.writer.close()
                raise

        await self.writer.drain()
        self.writer.close()

    async def process_publish(self, ident, chan, payload):
        if not ident == self.ak:
            raise BadClient(f"Invalid authkey in message, ident={ident}")

        if chan not in self.pubchans:
            raise BadClient(
                f'Authkey not allowed to pub here. ident={ident}, chan={chan}'
            )

        await self.server.publish(self, chan, payload)

    async def process_subscribe(self, ident, chan):
        if chan not in self.subchans:
            raise BadClient(
                f'Authkey not allowed to sub here. ident={ident}, chan={chan}'
            )

        await self.server.do_subscribe(self, ident, chan)

    async def process_unsubscribe(self, ident, chan):
        await self.server.do_unsubscribe(self, ident, chan)

    async def process_incoming_single(self):
        opcode, data = await self.reader.read_message()
        if opcode == OP_PUBLISH:
            await self.process_publish(*readpublish(data))
        elif opcode == OP_SUBSCRIBE:
            await self.process_subscribe(*readsubscribe(data))
        elif opcode == OP_UNSUBSCRIBE:
            await self.process_unsubscribe(*readsubscribe(data))
        else:
            raise BadClient((
                'Known opcode at unexpected moment '
                '(opcode={opcode}, len={data_length})'
            ))

    async def _process_incoming(self):
        try:
            opcode, data = await self.reader.read_message()
            if opcode != OP_AUTH:
                raise BadClient('First message was not AUTH')

            self.authkey_check(*readauth(data))

            while self.active:
                await self.process_incoming_single()

        except BadClient as e:
            await self.write(msgerror(str(e)))
            self.active = False

    async def handle(self):
        self.writer.write(msginfo(self.server.name, self.authrand))

        process_tasks = asyncio.gather(
            self._process_send_queue(),
            self._process_incoming(),
            )

        try:
            await process_tasks
        except asyncio.CancelledError:
            self.active = False
            await process_tasks
            # await process_tasks.cancel()

        self.active = False

    def authkey_check(self, ident, rhash):
        akrow = self.server.get_authkey(ident)
        if not akrow:
            raise BadClient(f"Authentication failed for {ident}")

        akhash = hashsecret(self.authrand, akrow["secret"])
        if not akhash == rhash:
            raise BadClient(f"Authentication failed for {ident}")

        self.ak = ident
        self.uid = akrow["owner"]
        self.pubchans = akrow.get("pubchans", [])
        self.subchans = akrow.get("subchans", [])
