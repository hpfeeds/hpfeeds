import json
import logging

from hpfeeds.broker.utils.inotify import start_watching

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

    async def start(self):
        close = start_watching(self.path, self.load)

        # If start_watching is unavailable, load the user data at least once at startup
        if not close:
            self.load()
            return

        return close

    def load(self):
        logger.info("Attempting to reload user database")

        try:
            with open(self.path, "r") as fp:
                db = json.load(fp)
        except Exception:
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
