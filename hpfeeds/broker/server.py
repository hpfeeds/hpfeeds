#!/usr/bin/python
# -*- coding: utf8 -*-

import asyncio
import collections
import logging
import re
import socket
import ssl

from .connection import Connection
from .prometheus import (
    CLIENT_SEND_BUFFER_FILL,
    RECEIVE_PUBLISH_COUNT,
    RECEIVE_PUBLISH_SIZE,
    SUBSCRIPTIONS,
    start_metrics_server,
)
from .utils.inotify import start_watching

log = logging.getLogger("hpfeeds.broker")


class Server(object):

    def __init__(self, auth, exporter=None, name='hpfeeds'):
        self.auth = auth
        self.name = name

        self.endpoints = []

        self.exporter = self._parse_endpoint(exporter)

        self.connections = set()
        self.subscriptions = collections.defaultdict(list)

        self.cleanups = []

        self.when_started = asyncio.Future()

    def add_endpoint_test(self, sock, ssl_context=None):
        self.endpoints.append({
            'class': 'test',
            'sock': sock,
            'ssl_context': ssl_context,
        })

    def add_endpoint_legacy(self, bind, tlscert=None, tlskey=None):
        interface, port = self._parse_endpoint(bind)
        endpoint = {
            'class': 'tcp' if not tlscert else 'tls',
            'interface': interface,
            'port': port,
        }
        if tlscert:
            endpoint.update({
                'cert': tlscert,
                'key': tlskey,
            })
        self.endpoints.append(endpoint)

    def add_endpoint_str(self, endpoint_str):
        """
        Like a twisted endpoint string.

        tcp:interface=1.1.1.1:port=80:device=eth0
        tls:interface=1.1.1.1:port=443:device=eth0:privateKey=path:cert=path:chain=path
        """
        tokens = re.split(r"(?<!\\):", endpoint_str)
        kls, tokens = tokens[0], tokens[1:]
        params = {"class": kls}
        for token in tokens:
            key, value = token.split("=", 1)
            params[key] = value
        self.endpoints.append(params)

    def _parse_endpoint(self, endpoint):
        if not endpoint:
            return (None, None)
        elif ':' not in endpoint:
            raise ValueError('Invalid bind addr')
        else:
            return endpoint.split(':', 1)

    def get_authkey(self, identifier):
        return self.auth.get_authkey(identifier)

    def publish(self, source, chan, data):
        '''
        Called by a connection to push data to all subscribers of a channel
        '''
        RECEIVE_PUBLISH_COUNT.labels(source.ak, chan).inc()
        RECEIVE_PUBLISH_SIZE.labels(source.ak, chan).observe(len(data))

        for dest in self.subscriptions[chan]:
            CLIENT_SEND_BUFFER_FILL.labels(dest.ak).inc(len(data))
            dest.publish(source.ak, chan, data)

    def subscribe(self, source, chan):
        '''
        Subscribe a connection to a channel
        '''
        SUBSCRIPTIONS.labels(source.ak, chan).inc()
        self.subscriptions[chan].append(source)
        source.active_subscriptions.add(chan)

    def unsubscribe(self, source, chan):
        '''
        Unsubscribe a connection from a channel
        '''
        if chan in source.active_subscriptions:
            source.active_subscriptions.remove(chan)
        if source in self.subscriptions[chan]:
            self.subscriptions[chan].remove(source)
        SUBSCRIPTIONS.labels(source.ak, chan).dec()

    def create_ssl_context(self, endpoint):
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        def load():
            cert = endpoint.get('cert', 'cert.pem')
            key = endpoint.get('key', 'key.pem')
            log.info("Loading certificate chain: {} / {}".format(cert, key))
            ssl_context.load_cert_chain(cert, key)

        cert_watcher = start_watching(endpoint.get('cert', 'cert.pem'), load)
        if cert_watcher:
            self.cleanups.append(cert_watcher)
        else:
            load()
            log.warning("Failed to watch certificate: {}".format(endpoint.get('cert', 'cert.pem')))
            log.warning("You may need to restart hpfeeds-broker to get certificate changes detected")

        key_watcher = start_watching(endpoint.get('key', 'key.pem'), load)
        if key_watcher:
            self.cleanups.append(key_watcher)
        else:
            load()
            log.warning("Failed to watch private key: {}".format(endpoint.get('key', 'key.pem')))
            log.warning("You may need to restart hpfeeds-broker to get private key changes detected")

        return ssl_context

    async def serve_forever(self):
        ''' Start handling connections. Await on this to listen forever. '''

        try:
            auth_finalizer = await self.auth.start()

            if self.exporter:
                metrics_server = await start_metrics_server(*self.exporter)
                metrics_server.app.broker = self

            servers = []

            for endpoint in self.endpoints:
                ssl_context = None

                if endpoint['class'] == 'tls':
                    ssl_context = self.create_ssl_context(endpoint)

                if endpoint['class'] == 'test':
                    sock = endpoint['sock']
                    ssl_context = endpoint['ssl_context']
                else:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.bind((endpoint.get('interface', '0.0.0.0'), int(endpoint['port'])))

                # Allow user to use SO_BINDTODEVICE
                # E.g. you could run 2 endpoints - one with and one without TLS, and bind the LAN side to an internal NIC.
                # Usage: tls:interface=0.0.0.0:port=20001:device=eth0
                if 'device' in endpoint:
                    device = endpoint['device'][:15].encode('utf-8') + b'\0'
                    sock.setsockopt(socket.SOL_SOCKET, 25, device)

                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

                endpoint['port'] = sock.getsockname()[1]

                servers.append(await asyncio.get_event_loop().create_server(
                    lambda: Connection(self),
                    sock=sock,
                    ssl=ssl_context,
                ))

            self.when_started.set_result(None)

            await asyncio.Event().wait()

        except asyncio.CancelledError:
            pass

        except Exception:
            log.exception("Unhandled exception whilst starting server")

        finally:
            [s.close() for s in servers]

            for cleanup in self.cleanups:
                await cleanup()

            # for future in asyncio.as_completed([c.close() for c in list(self.connections)]):
            #    try:
            #        await future
            #    except Exception as e:
            #        log.exception(e)

            log.debug(f'Waiting for {self} to wrap up')
            for server in servers:
                await server.wait_closed()

            if self.exporter:
                log.debug('Waiting for stats server to wrap up')
                await metrics_server.cleanup()

            if auth_finalizer:
                log.debug('Waiting for auth db to close')
                await auth_finalizer()
