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


def resolve(path, strict=False):
    sep = os.path.sep
    seen = {}

    found = [path]

    def _resolve(path, rest):
        if rest.startswith(sep):
            path = ''

        for name in rest.split(sep):
            if not name or name == '.':
                # current dir
                continue
            if name == '..':
                # parent dir
                path, _, _ = path.rpartition(sep)
                continue
            newpath = path + sep + name
            if newpath in seen:
                # Already seen this path
                path = seen[newpath]
                if path is not None:
                    # use cached value
                    continue
                # The symlink is not resolved, so we must have a symlink loop.
                raise RuntimeError("Symlink loop from %r" % newpath)

            found.append(newpath)

            # Resolve the symbolic link
            try:
                target = os.readlink(newpath)
            except OSError as e:
                from errno import EINVAL
                if e.errno != EINVAL and strict:
                    raise
                # Not a symlink, or non-strict mode. We just leave the path
                # untouched.
                path = newpath
            else:
                # found.append(newpath)
                seen[newpath] = None  # not resolved symlink
                path = _resolve(path, target)
                seen[newpath] = path  # resolved symlink

        return path

    # NOTE: according to POSIX, getcwd() cannot contain path components
    # which are symlinks.
    base = '' if os.path.isabs(path) else os.getcwd()
    found.append(_resolve(base, str(path)) or sep)

    return found


class Authenticator(object):

    def __init__(self, path):
        self.path = path
        self.db = {}

    async def _watch_until_exception(self):
        if not os.path.exists(self.path):
            return

        watcher = aionotify.Watcher()
        await watcher.setup(asyncio.get_event_loop())

        paths = set()
        try:
            while True:
                old_paths = paths

                # Find all paths related to self.path (resolving symlinks as we go)
                paths = set(resolve(self.path))

                # Unwatch old paths
                for path in (old_paths - paths):
                    logger.debug(f"Unwatching {path!r}")
                    watcher.unwatch(path)

                # Watch new paths
                for path in (paths - old_paths):
                    logger.debug(f"Watching {path!r}")
                    watcher.watch(
                        path=path,
                        flags=aionotify.Flags.MODIFY | aionotify.Flags.ATTRIB | aionotify.Flags.MOVE_SELF | aionotify.Flags.DONT_FOLLOW
                    )

                # Reload user database
                self.load()

                # Sleep until an event touches one of the paths we care about
                event = await watcher.get_event()

                # We have to rewatch the file that changed because we care about atomic renames
                # Because we are watching a handle, an atomic rename means handle will now point
                # somewhere else entirely and we'll not detect future changes
                logger.debug(f"Detected change in {event.alias!r} - rewatching")
                watcher.unwatch(event.alias)
                watcher.watch(
                    path=event.alias,
                    flags=aionotify.Flags.MODIFY | aionotify.Flags.ATTRIB | aionotify.Flags.MOVE_SELF | aionotify.Flags.DONT_FOLLOW
                )

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
