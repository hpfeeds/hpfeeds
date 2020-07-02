import logging

# An authenticator that calls out to other authenticators


logger = logging.getLogger(__name__)


class Authenticator(object):

    def __init__(self):
        self.stack = []

    def add(self, authenticator):
        self.stack.append(authenticator)

    async def start(self):
        for stack in self.stack:
            await stack.start()
        logger.info("%d authenticators have been started.", len(self.stack))

    def close(self):
        for stack in self.stack:
            stack.close()

    def get_authkey(self, ident):
        for stack in self.stack:
            result = stack.get_authkey(ident)
            if result:
                return result
        return None
