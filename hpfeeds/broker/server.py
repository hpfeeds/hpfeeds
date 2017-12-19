#!/usr/bin/python
# -*- coding: utf8 -*-

import gevent.monkey
gevent.monkey.patch_all()  # noqa: E402

import collections
import os
import logging

import gevent
import gevent.server

from hpfeeds.broker.auth import sqlite
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


log = logging.getLogger("broker")


class Connection(object):

    def __init__(self, sock, addr, srv):
        self.sock = sock
        self.addr = addr
        self.srv = srv
        self.uid = None
        self.ak = None
        self.pubchans = []
        self.subchans = []
        self.active = True
        self.unpacker = Unpacker()

    def __del__(self):
        # if this message is not showing up we're leaking references
        log.debug("Connection cleanup {0}".format(self.addr))

    def write(self, data):
        try:
            self.sock.sendall(data)
            #  self.stats['bytes_sent'] += len(data)
        except Exception as e:
            log.critical('Exception when writing to conn', exc_info=e)

    def handle(self):
        # first send the info message
        self.authrand = authrand = os.urandom(4)
        self.write(msginfo(config.FBNAME, authrand))

        while True:
            self.unpacker.feed(self.s.recv(BUFSIZ))
            for opcode, data in self.unpacker:
                if opcode != OP_AUTH:
                    self.error('First message was not AUTH.')
                    raise BadClient()

                ident, rhash = readauth(data)
                self.authkey_check(ident, rhash)
                break

        while True:
            self.unpacker.feed(self.recv(BUFSIZ))

            for opcode, data in self.unpacker:
                if opcode == OP_PUBLISH:
                    self.do_publish(*readpublish(data))
                elif opcode == OP_SUBSCRIBE:
                    self.do_subscribe(*readsubscribe(data))
                elif opcode == OP_UNSUBSCRIBE:
                    self.do_unsubscribe(*readsubscribe(data))
                else:
                    self.error(
                        "Unknown message type.",
                        opcode=opcode,
                        length=len(data),
                    )
                    raise BadClient()

    def do_publish(self, ident, chan, payload):
        if not ident == self.ak:
            self.error("Invalid authkey in message.", ident=ident)
            raise BadClient()

        if chan not in self.pubchans or chan.endswith("..broker"):
            self.error(
                "Authkey not allowed to publish here.",
                chan=chan
            )
            return

        self.srv.do_publish(self, chan, payload)
        #  self.stats["published"] += 1

    def do_subscribe(self, ident, chan):
        checkchan = chan
        if chan.endswith('..broker'):
            checkchan = chan.rsplit('..broker', 1)[0]

        if checkchan not in self.subchans:
            self.error(
                "Authkey not allowed to subscribe here.",
                chan=chan,
            )
            return

        self.srv.do_subscribe(self, ident, chan)

    def do_unsubscribe(self, ident, chan):
        self.do_unsubscribe(self, ident, chan)

    def authkey_check(self, ident, rhash):
        akrow = self.srv.get_authkey(ident)
        if not akrow:
            self.error("Authentication failed.", ident=ident)
            raise BadClient()

        akhash = hashsecret(self.authrand, akrow["secret"])
        if not akhash == rhash:
            self.error("Authentication failed.", ident=ident)
            raise BadClient()

        self.ak = ident
        self.uid = akrow["owner"]
        self.pubchans = akrow.get("pubchans", [])
        self.subchans = akrow.get("subchans", [])

    def forward(self, ident, chan, data):
        self.write(msgpublish(ident, chan, data))
        #  self.stats['received'] += 1

    def error(self, msg, *args, **context):
        emsg = msg.format(*args)
        log.critical(emsg)
        self.srv.log_error(emsg, self, context)
        self.write(msgerror(emsg))


class Server(object):

    def __init__(self):
        self.listener = gevent.server.StreamServer(
            (config.FBIP, config.FBPORT),
            self._newconn,
            **config.SSLOPTS
        )
        self.db = self.dbclass()
        self.connections = set()
        self.subscribermap = collections.defaultdict(list)
        self.conn2chans = collections.defaultdict(list)

    def dbclass(self):
        return sqlite.Authenticator('db.sqlite3')

    def connclass(self, *args):
        return Connection(*args)

    def serve_forever(self):
        log.info("StreamServer ssl_enabled=%s", str(self.listener.ssl_enabled))
        self.listener.serve_forever()

    def _newconn(self, sock, addr):
        log.debug('Connection from {0}.'.format(addr))
        fc = self.connclass(sock, addr, self)
        self.connections.add(fc)

        try:
            fc.handle()
        except Disconnect:
            log.debug("Connection closed by {0}".format(addr))
        except BadClient:
            log.warn('Connection ended due to bad client: {0}'.format(addr))

        fc.active = False

        for chan in self.conn2chans[fc]:
            self.subscribermap[chan].remove(fc)
            if fc.ak:
                self._brokerchan(fc, chan, fc.ak, 'leave')

        del self.conn2chans[fc]

        self.connections.remove(fc)
        try:
            sock.close()
        except Exception:
            pass

    def do_publish(self, c, chan, data):
        log.debug('publish to {0} by {1} ak {2} addr {3}'.format(
            chan, c.uid, c.ak, c.addr
        ))
        try:
            for c2 in self.receivers(chan, c, self.subscribermap[chan]):
                c2.forward(c.ak, chan, data)
        except Exception as e:
            log.exception('Error publishing payload')

    def do_subscribe(self, c, ident, chan):
        log.debug('broker subscribe to {0} by {1}@{2}'.format(
            chan, ident, c.addr
        ))
        self.subscribermap[chan].append(c)
        self.conn2chans[c].append(chan)
        if not chan.endswith('..broker'):
            self._brokerchan(c, chan, ident, 'join')

    def do_unsubscribe(self, c, ident, chan):
        log.debug('broker unsubscribe to {0} by {1}@{2}'.format(
            chan, ident, c.addr
        ))
        self.subscribermap[chan].remove(c)
        self.conn2chans[c].remove(chan)
        if not chan.endswith('..broker'):
            self._brokerchan(c, chan, ident, 'leave')

    def _brokerchan(self, c, chan, ident, data):
        brokchan = chan + '..broker'
        try:
            for c2 in self.receivers(chan, c, self.subscribermap[brokchan]):
                c2.publish(ident, chan, data)
        except Exception as e:
            log.exception('Error publishing to broker channels')

    def log_error(self, emsg, conn, context):
        return self.db.log({
            "msg": emsg,
            "ip": conn.addr[0],
            "user": conn.uid,
            "authkey": conn.ak,
            "context": context,
        })

    def get_authkey(self, identifier):
        return self.db.get_authkey(identifier)

    def receivers(self, chan, conn, subscribed_conns):
        if not subscribed_conns:
            return

        # this is plain hpfeeds mode, no graph
        # all subscribed connections allowed to receive by default
        for c in subscribed_conns:
            yield c
