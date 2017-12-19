import logging

from hpfeeds.broker.server import Server


def main():
    logging.basicConfig(level=logging.DEBUG if config.DEBUG else logging.INFO)
    s = Server()
    s.serve_forever()
    return 0
