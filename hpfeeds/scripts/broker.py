import argparse
import logging

import aiorun

from hpfeeds.broker.auth import env, sqlite
from hpfeeds.broker.server import Server


def main():
    parser = argparse.ArgumentParser(description='Run a hpfeeds broker')
    parser.add_argument('--bind', default='0.0.0.0:20000', action='store')
    parser.add_argument('--exporter', default='', action='store')
    parser.add_argument('--name', default='hpfeeds', action='store')
    parser.add_argument('--debug', default=False, action='store_true')
    parser.add_argument('--auth', default='sqlite', action='store')
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
    )

    if args.auth == 'env':
        auth = env.Authenticator()
    else:
        auth = sqlite.Authenticator('sqlite.db')

    broker = Server(
        auth=auth,
        bind=args.bind,
        exporter=args.exporter,
        name=args.name,
    )

    return aiorun.run(broker.serve_forever())


if __name__ == '__main__':
    main()
