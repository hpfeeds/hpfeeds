#!/usr/bin/python
# -*- coding: utf8 -*-

import sys
import logging

from broker import Server, Connection
import config

log = logging.getLogger("testbroker")

class TestServer(Server):
    def dbclass(self):
        return None

    def connclass(self, *args):
        return TestConnection(*args)

    def log_error(self, emsg, conn, context):
        return None

    def connstats(self, *args, **kwargs):
        return None

class TestConnection(Connection):
    def authkey_check(self, ident, rhash):
        # no check
        self.ak = ident
        self.uid = "testuid"

    def may_publish(self, chan):
        return True

    def may_subscribe(self, chan):
        return True

def main():
    logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO)
    log.info("broker starting up...")
    s = TestServer()
    s.serve_forever()
    return 0

if __name__ == '__main__':
    try: sys.exit(main())
    except KeyboardInterrupt: pass
