import argparse
import logging

import aiorun

from hpfeeds.broker.auth import env, json, sqlite
from hpfeeds.broker.server import Server


def main():
    parser = argparse.ArgumentParser(description='Run a hpfeeds broker')
    parser.add_argument('--bind', default=None, action='store')
    parser.add_argument('--exporter', default='', action='store')
    parser.add_argument('--name', default='hpfeeds', action='store')
    parser.add_argument('--debug', default=False, action='store_true')
    parser.add_argument('--auth', default='sqlite', action='store')
    parser.add_argument('--tlscert', default=None, action='store')
    parser.add_argument('--tlskey', default=None, action='store')
    parser.add_argument('-e', '--endpoint', default=None, action='append')
    args = parser.parse_args()

    if (args.tlscert and not args.tlskey) or (args.tlskey and not args.tlscert):
        parser.error('Must specify --tlskey AND --tlscert')
        return

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
    )

    if args.auth.endswith('.json'):
        auth = json.Authenticator(args.auth)
    elif args.auth == 'env':
        auth = env.Authenticator()
    else:
        auth = sqlite.Authenticator('sqlite.db')

    broker = Server(
        auth=auth,
        exporter=args.exporter,
        name=args.name,
    )

    if args.bind or not args.endpoint:
        bind = args.bind or '0.0.0.0:20000'
        broker.add_endpoint_legacy(bind, tlscert=args.tlscert, tlskey=args.tlskey)

    if args.endpoint:
        for endpoint in args.endpoint:
            broker.add_endpoint_str(endpoint)

    return aiorun.run(broker.serve_forever())


if __name__ == '__main__':
    main()
