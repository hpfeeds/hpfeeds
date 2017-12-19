# Copyright (C) 2010-2013 Mark Schloesser <ms@mwcollect.org
# This file is part of hpfeeds - https://github.com/rep/hpfeeds
# See the file 'LICENSE' for copying permission.

import struct
import hashlib


BUFSIZ = 16384

OP_ERROR = 0
OP_INFO = 1
OP_AUTH = 2
OP_PUBLISH = 3
OP_SUBSCRIBE = 4

MAXBUF = 1024**2

SIZES = {
    OP_ERROR: 5 + MAXBUF,
    OP_INFO: 5 + 256 + 20,
    OP_AUTH: 5 + 256 + 20,
    OP_PUBLISH: 5 + MAXBUF,
}


class ProtocolError(Exception):
    pass


def force_bytes(value):
    if isinstance(value, str):
        return value.encode('utf-8')
    return value


def force_str(value):
    if isinstance(value, bytes):
        return value.decode('utf-8')
    return value


def strpack8(x):
    # packs a string with 1 byte length field
    x = force_bytes(x)
    return struct.pack('!B', len(x)) + x


def strunpack8(x):
    # unpacks a string with 1 byte length field
    length = x[0]
    return force_str(x[1:1+length]), x[1+length:]


def msghdr(op, data):
    return struct.pack('!iB', 5 + len(data), op) + data


def msgsubscribe(ident, chan):
    return msghdr(OP_SUBSCRIBE, strpack8(ident) + force_bytes(chan))


def msgpublish(ident, chan, data):
    return msghdr(
        OP_PUBLISH,
        strpack8(ident) + strpack8(chan) + force_bytes(data),
    )


def msgauth(rand, ident, secret):
    hash = hashlib.sha1(bytes(rand) + secret.encode('utf-8')).digest()
    return msghdr(OP_AUTH, strpack8(ident) + hash)


def readsubscribe(data):
    ident, rest = strunpack8(data)
    return ident, force_str(rest)


def readpublish(data):
    ident, rest = strunpack8(data)
    chan, rest = strunpack8(rest)
    return ident, chan, rest


class Unpacker(object):

    def __init__(self):
        self.buf = bytearray()

    def __iter__(self):
        return self

    def __next__(self):
        return self.unpack()

    def feed(self, data):
        self.buf.extend(data)

    def unpack(self):
        if len(self.buf) < 5:
            raise StopIteration('No message.')

        ml, opcode = struct.unpack('!iB', self.buf[0:5])
        if ml > SIZES.get(opcode, MAXBUF):
            raise ProtocolError('Not respecting MAXBUF.')

        if len(self.buf) < ml:
            raise StopIteration('No message.')

        data = bytearray(self.buf[5:])
        del self.buf[:ml]
        return opcode, data
