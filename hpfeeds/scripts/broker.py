import argparse
import logging

import aiorun

from hpfeeds.broker.auth import sqlite
from hpfeeds.broker.server import Server


def main():
    parser = argparse.ArgumentParser(description='Run a hpfeeds broker')
    parser.add_argument('--host', default='0.0.0.0', action='store')
    parser.add_argument('--port', default='20000', action='store')
    parser.add_argument('--name', default='hpfeeds', action='store')
    parser.add_argument('--debug', default=False, action='store_true')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
    )

    broker = Server(
        auth=sqlite.Authenticator('sqlite.db'),
        host=args.host,
        port=args.port,
        name=args.name,
    )

    return aiorun.run(broker.serve_forever())


if __name__ == '__main__':
    main()
