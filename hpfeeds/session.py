import errno
import logging
import os
import select
import socket
import sys
import threading

from hpfeeds.exceptions import ProtocolException
from hpfeeds.protocol import (
    OP_ERROR,
    OP_INFO,
    OP_PUBLISH,
    Unpacker,
    msgauth,
    msgpublish,
    msgsubscribe,
    msgunsubscribe,
    readerror,
    readinfo,
    readpublish,
)

try:
    import queue
except ImportError:
    import Queue as queue


class Queue(queue.Queue, object):

    def __init__(self):
        super(Queue, self).__init__()
        # Create a pair of connected sockets
        if os.name == 'posix':
            self._putsocket, self._getsocket = socket.socketpair()
        else:
            # Compatibility on non-POSIX systems
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.bind(('127.0.0.1', 0))
            server.listen(1)
            self._putsocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._putsocket.connect(server.getsockname())
            self._getsocket, _ = server.accept()
            server.close()

    def fileno(self):
        return self._getsocket.fileno()

    def put(self, item, block=True):
        super(Queue, self).put(item, block)
        self._putsocket.send(b'x')

    def get(self, block=True):
        self._getsocket.recv(1)
        return super(Queue, self).get(block)


class BaseProtocol(object):

    def __init__(self, reactor, ident, secret):
        self.reactor = reactor
        self.ident = ident
        self.secret = secret
        self.unpacker = Unpacker()

    def connection_made(self):
        pass

    def connection_ready(self):
        pass

    def protocol_error(self, reason):
        pass

    def _on_error(self, error):
        raise ProtocolException(error)

    def _on_info(self, name, rand):
        self.reactor.write(msgauth(rand, self.ident, self.secret))
        self.connection_ready()

    def _on_publish(self, ident, chan, data):
        raise NotImplementedError(self.on_publish)

    def message_received(self, opcode, data):
        if opcode == OP_ERROR:
            return self._on_error(readerror(data))
        elif opcode == OP_INFO:
            return self._on_info(*readinfo(data))
        elif opcode == OP_PUBLISH:
            return self._on_publish(*readpublish(data))

        # Can't recover from an unknown opcode, so drop connection
        self.protocol_error('Unknown message opcode: {!r}'.format(opcode))
        self.reactor.close()

    def data_received(self, data):
        self.unpacker.feed(data)
        for opcode, data in self.unpacker:
            self.message_received(opcode, data)


class Reactor(object):

    '''
    This class handles IO multiplexing and connection failure handling.
    '''

    def __init__(self, protocol_class, connector):
        self.protocol_class = protocol_class
        self.connector = connector

        self.closing = False
        self.when_connected = threading.Event()

        self._outbox = Queue()

    def write(self, data):
        self._outbox.put_nowait(data)

    def close(self):
        self.sock.close()

    def _connect(self):
        '''
        Establish a connection using ``self.connector`` and then set up
        internal state for that new connection.
        '''
        self.sock = self.connector()

        self.sock.setblocking(False)

        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        if sys.platform.startswith('linux'):
            self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPIDLE, 10)
            self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPINTVL, 5)
            self.sock.setsockopt(socket.SOL_TCP, socket.TCP_KEEPCNT, 3)

        self._buffer = b''
        self._outbox = Queue()

        self.protocol = self.protocol_class(self, 'test', 'test')
        self.protocol.connection_made()

        self.when_connected.set()

    def _select(self):
        '''
        Block (and don't consume CPU) until self.sock or self._outbox is ready
        for us
        '''
        want_read = [self.sock]
        want_write = []

        if self._buffer:
            want_write.append(self.sock)
        else:
            want_read.append(self._outbox)

        print(want_read, want_write)
        r, w, x = select.select(want_read, want_write, [])

        if self.sock in r and not self._socket_read_ready():
            return

        if self._outbox in r and not self._outbox_read_ready():
            return

        if self.sock in w and not self._socket_write_ready():
            return

    def _socket_read_ready(self):
        try:
            data = self.sock.recv(1024)
        except socket.error as e:
            # Interupted by.. interupt, try again
            if e.args[0] == errno.EAGAIN:
                return True

            # Would block, so return and go back to sleep
            if e.args[0] == errno.EWOULDBLOCK:
                return True

            raise

        if not data:
            self._connection_lost('Read failed')
            return False

        self.protocol.data_received(data)
        return True

    def _outbox_read_ready(self):
        try:
            self._buffer += self._outbox.get_nowait()
        except socket.error as e:
            # Interupted by.. interupt, try again
            if e.args[0] == errno.EAGAIN:
                return True

            # Would block, so return and go back to sleep
            if e.args[0] == errno.EWOULDBLOCK:
                return True
        except queue.Empty:
            # Someone lied - there is no data really
            # Go to sleep and try again later
            return True

        # If we were blocked waiting for something to land in queue there is
        # good chance the write socket is ready. Try to send.
        self._socket_write_ready()

    def _socket_write_ready(self):
        try:
            sent = self.sock.send(self._buffer)
        except socket.error as e:
            # Interupted by.. interupt, try again
            if e.args[0] == errno.EAGAIN:
                return True

            # Would block, so return and go back to sleep
            if e.args[0] == errno.EWOULDBLOCK:
                return True

            raise

        if sent == 0:
            self._connection_lost('Write failed')
            return False

        self._buffer = self._buffer[sent:]
        return True

    def _connection_lost(self, reason):
        self.proto.connection_lost(reason)
        try:
            self.sock.close()
        except Exception:
            pass
        self.sock = None
        self.when_connected.clear()

    def run_forever(self):
        while not self.closing:
            self._connect()

            while not self.closing:
                self._select()

    def stop(self):
        self.closing = True
        if self.sock:
            self._connection_lost('Client session terminated')


class ThreadReactor(Reactor):

    def start(self):
        self._thread = threading.Thread(target=self.run_forever)
        self._thread.start()

    def stop(self):
        super(ThreadReactor, self).stop()
        self._thread.join()


class Protocol(BaseProtocol):

    def on_publish(self, ident, channel, payload):
        self._inbox.put_nowait((ident, channel, payload))


class ClientSession(object):

    '''
    Create and maintain a session with the hpfeeds broker.

    The connection is managed in a dedicated thread.
    '''

    def __init__(self, host, port, ident, secret):
        self.host = host
        self.port = port
        self.ident = ident
        self.secret = secret

        self._reactor = ThreadReactor(
            Protocol,
            self.connect,
        )

        self.subscriptions = set()

    def connect(self):
        while True:
            logging.debug("Starting connection attempt")
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.connect((self.host, self.port))
            except Exception as e:
                logging.exception(e)
                continue

            return sock

    def start(self):
        self._reactor.start()

    def stop(self):
        self._reactor.stop()

    def publish(self, channel, payload):
        self._reactor.write(msgpublish(self.ident, channel, payload))

    def publish_iter(self, channel, iterator):
        for payload in iterator:
            self.publish(channel, payload)

    def subscribe(self, channel):
        self.subscriptions.add(channel)
        self._reactor.write(msgsubscribe(self.ident, channel))

    def unsubscribe(self, channel):
        self.subscriptions.discard(channel)
        self._reactor.write(msgunsubscribe(self.ident, channel))

    def read(self):
        return self.read_queue.get()

    def __enter__(self):
        self.start()
        self._reactor.when_connected.wait()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def __iter__(self):
        return self

    def __next__(self):
        if self._reactor.closing:
            raise StopIteration()
        return self.read()

    def next(self):
        return self.__next__()
