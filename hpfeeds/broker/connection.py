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


log = logging.getLogger("hpfeeds.connection")


class Connection(object):

    def __init__(self, server, reader, writer):
        self.server = server
        self.reader = reader
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
        return f'<Connection ident={self.ak} owner={self.uid} peer={peer} port={port}'

    async def write(self, message):
        await self.send_queue.put(message)

    async def process_send_queue(self):
        while self.active:
            try:
                self.writer.write(await self.send_queue.get())
            except Exception as e:
                self.active = False
                writer.close()
                raise

        self.writer.write(msgerror('Connection closed'))
        await self.writer.drain()
        writer.close()

    async def process_publish(self, ident, chan, payload):
        if not ident == self.ak:
            raise BadClient(f"Invalid authkey in message, ident={ident}")

        if chan not in self.pubchans:
            raise BadClient(f"Authkey not allowed to publish here. ident={ident}, chan={chan}")

        await self.server.publish(self, chan, payload)

    async def process_subscribe(self, ident, chan):
        if chan not in self.subchans:
            raise BadClient(f"Authkey not allowed to subscribe here. ident={ident}, chan={chan}")

        await self.server.do_subscribe(self, ident, chan)

    async def process_unsubscribe(self, ident, chan):
        await self.server.do_unsubscribe(self, ident, chan)

    async def process_incoming(self):
        while self.active:
            data = await self.reader.read(BUFSIZ)
            if not data:
                self.active = False
                break

            self.unpacker.feed(data)

            for opcode, data in self.unpacker:
                if opcode != OP_AUTH:
                    raise BadClient('First message was not AUTH.')
                ident, rhash = readauth(data)
                self.authkey_check(ident, rhash)
                break

        while self.active:
            data = await self.reader.read(BUFSIZ)
            if not data:
                self.active = False
                break

            self.unpacker.feed(data)

            for opcode, data in self.unpacker:
                if opcode == OP_PUBLISH:
                    await self.process_publish(*readpublish(data))
                elif opcode == OP_SUBSCRIBE:
                    await self.process_subscribe(*readsubscribe(data))
                elif opcode == OP_UNSUBSCRIBE:
                    await self.process_unsubscribe(*readsubscribe(data))
                else:
                    raise BadClient('Unknown message type (opcode={opcode}, len={data_length})')

    async def handle(self):
        self.writer.write(msginfo(self.server.name, self.authrand))

        process_tasks = asyncio.gather(
            self.process_send_queue(),
            self.process_incoming(),
            )

        try:
            await process_tasks
        except asyncio.CancelledError:
            self.active = False
            await process_tasks
            #await process_tasks.cancel()

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
