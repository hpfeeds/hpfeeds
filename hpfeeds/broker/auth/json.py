import asyncio
import json
import logging
import os

try:
    import aionotify
except ImportError:
    aionotify = None


# An authenticator where the data is backed by JSON:

# {
#   "bob": {
#      "owner": "bob",
#      "secret": "secret",
#      "pubchans": ["chan1"],
#      "subchans": ["chan1"]
#   }
# }

logger = logging.getLogger(__name__)


class Authenticator(object):

    def __init__(self, path):
        self.path = path
        self.db = {}

    async def _watch_until_exception(self):
        if not os.path.exists(self.path):
            return

        watcher = aionotify.Watcher()
        watcher.watch(path=os.path.dirname(self.path), flags=aionotify.Flags.MODIFY | aionotify.Flags.MOVED_FROM | aionotify.Flags.MOVED_TO)
        await watcher.setup(asyncio.get_event_loop())

        try:
            # We do a load here to avoid races where the data changes before the watcher was setup
            self.load()

            while True:
                event = await watcher.get_event()
                if event.name != os.path.basename(self.path):
                    continue
                self.load()
        finally:
            watcher.close()

    async def _watch_forever(self):
        while True:
            try:
                await self._watch_until_exception()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(f"Error whilst monitoring {self.path!r} for changes")
                await asyncio.sleep(1)
                continue

    async def start(self):
        if not aionotify:
            self.load()
            logger.warning(f"Changes to {self.path!r} will require a broker restart as aionotify is not installed")
            return

        task = asyncio.ensure_future(self._watch_forever())

        async def close():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        return close

    def load(self):
        logger.info("Attempting to reload user database")

        try:
            with open(self.path, "r") as fp:
                db = json.load(fp)
        except:
            logger.exception(f"Error whilst trying to load {self.path!r}")
            return

        if not isinstance(db, dict):
            logger.error("Authentication database root is not a mapping")
            return

        for key, value in db.items():
            if not isinstance(value, dict):
                logger.error(f"Authentication entry for {key!r} is not a mapping")
                return

            for attr in ("owner", "secret", "pubchans", "subchans"):
                if attr not in value:
                    logger.error(f"Authentication entry for {key!r} is missing key {attr!r}")
                    return

            for attr in ("pubchans", "subchans"):
                if not isinstance(value[attr], list):
                    logger.error(f"Authentication entry for {key!r} has wrong type for {attr!r} field (expected list)")
                    return

        self.db = db

        logger.info(f"User database reloaded, {len(self.db)} users loaded")

    def close(self):
        pass

    def get_authkey(self, ident):
        res = self.db.get(ident, None)
        if not res:
            return None

        return dict(
            secret=res["secret"],
            ident=ident,
            pubchans=res["pubchans"],
            subchans=res["subchans"],
            owner=res["owner"],
        )
