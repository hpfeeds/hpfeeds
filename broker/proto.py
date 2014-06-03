#!/usr/bin/python
# -*- coding: utf8 -*-

import struct
import logging

from utils import Disconnect, BadClient

OP_ERROR    = 0
OP_INFO     = 1
OP_AUTH     = 2
OP_PUBLISH  = 3
OP_SUBSCRIBE    = 4
OP_UNSUBSCRIBE  = 5

BUFSIZ = 16 * 1024
MAXBUF = 10 * (1024**2)

def msghdr(op, data):
    return struct.pack('!iB', 5+len(data), op) + data

def msginfo(name, rand):
    return msghdr(OP_INFO, '{0}{1}{2}'.format(chr(len(name)), name, rand))

def msgerror(emsg):
    return msghdr(OP_ERROR, emsg)

def msgpublish(ident, chan, data):
    return msghdr(OP_PUBLISH, chr(len(ident)) + ident + chr(len(chan)) + chan + data)

def recv(sock, minlength):
    buf = ""
    while len(buf) < minlength:
        try:
            tmp = sock.recv(minlength - len(buf))
        except (socket.error, socket.timeout):
            logging.critical("Exception when reading from sock: {0}".format(e))
            raise Disconnect()

        if not tmp:
            raise Disconnect()

        buf += tmp

    return buf

def read_message(sock):
    buf = recv(sock, 5)
    ml, opcode = struct.unpack('!iB', buf)

    if ml > MAXBUF:
        logging.critical("Client not respecting MAXBUF: {0}".format(sock.getpeername()))
        raise BadClient()

    buf = recv(sock, ml-5)
    nextlen, buf = ord(buf[0]), buf[1:]
    ident, buf = buf[:nextlen], buf[nextlen:]

    return opcode, ident, buf

def split(data, howmany):
    out = []
    rest = buffer(data, 0)

    while howmany:
        length = ord(rest[0])
        current, rest = rest[1:length+1], rest[length+1:]
        out.append(str(current))
        howmany -= 1

    out.append(str(rest))
    return out
