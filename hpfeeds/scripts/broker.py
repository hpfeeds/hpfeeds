import argparse
import logging
import sys

import aiorun

from hpfeeds.broker.auth import database, env, json, mongo, multi, sqlite
from hpfeeds.broker.server import Server, ServerException


def get_authenticator(auth):
    if auth.endswith('.json'):
        return json.Authenticator(auth)
    elif auth == 'env':
        return env.Authenticator()
    elif auth.startswith("mongo"):
        return mongo.Authenticator(auth)
    elif auth.startswith("database+"):
        return database.Authenticator(auth)
    return sqlite.Authenticator('sqlite.db')


def main():
    parser = argparse.ArgumentParser(description='Run a hpfeeds broker')
    parser.add_argument('--bind', default=None, action='store')
    parser.add_argument('--exporter', default='', action='store')
    parser.add_argument('--name', default='hpfeeds', action='store')
    parser.add_argument('--debug', default=False, action='store_true')
    parser.add_argument('--auth', default=None, action='append')
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

    auth = multi.Authenticator()
    auths = args.auth if args.auth else ['sqlite']
    for a in auths:
        try:
            auth.add(get_authenticator(a))
        except ServerException as e:
            print(str(e))
            sys.exit(1)

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
