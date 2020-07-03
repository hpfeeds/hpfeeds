import logging

# An authenticator that calls out to other authenticators


logger = logging.getLogger(__name__)


class Authenticator(object):

    def __init__(self):
        self.stack = []
        self.close_fn = []

    def add(self, authenticator):
        self.stack.append(authenticator)

    async def start(self):
        for stack in self.stack:
            close_fn = await stack.start()
            if not close_fn:
                continue
            self.close_fn.append(close_fn)

        logger.info("%d authenticators have been started.", len(self.stack))
        return self._close

    def _close(self):
        logger.info("Running all authenticator finalizers")
        for finalizer in self.close_fn:
            try:
                finalizer()
            except Exception:
                logger.exception("Unhandled error whilst shutting down authenticator")
        self.close_fn = []
        self.stack = []

    def get_authkey(self, ident):
        for stack in self.stack:
            result = stack.get_authkey(ident)
            if result:
                return result
        return None
