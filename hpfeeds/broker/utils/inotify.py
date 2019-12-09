import asyncio
import logging
import os

from .supervisor import supervise

try:
    import aionotify
except ImportError:
    aionotify = None


logger = logging.getLogger(__name__)

MODIFY_FLAGS = None

if aionotify:
    class Watcher(aionotify.Watcher):

        # https://github.com/rbarrois/aionotify/pull/6/files

        def forget_alias(self, alias):
            if alias not in self.descriptors:
                return
            wd = self.descriptors[alias]
            del self.descriptors[alias]
            del self.requests[alias]
            del self.aliases[wd]

        def unwatch(self, alias):
            try:
                super().unwatch(alias)
            except IOError:
                self.forget_alias(alias)

    MODIFY_FLAGS = (
        aionotify.Flags.MODIFY | aionotify.Flags.ATTRIB | aionotify.Flags.MOVE_SELF | aionotify.Flags.DONT_FOLLOW
    )


def _resolve_paths(path, strict=False):
    """
    This function finds constituent paths for a given path. For example, given a symlink far that
    looks like:

      /tmp/foo.json -> /tmp/_data/foo.json
      /tmp/_data -> /tmp/_1
      /tmp/_1/foo.json (actual file)

    Then we dont just want to watch /tmp/foo.json and we don't just want to watch
    /tmp/_1/foo.json, we need to watch /tmp/_data too. So this function would return:

      ["/tmp", "/tmp/_data", "/tmp/foo.json", "/tmp/_1/foo.json", "/tmp_1"]

    Note that "/tmp/_data/foo.json is **not** returned, as its not actually a real path that
    is distinct from the paths we did return.
    """
    seen = {}

    found = [path]

    def _resolve(path, rest):
        if rest.startswith(os.path.sep):
            path = ''

        for name in rest.split(os.path.sep):
            if not name or name == '.':
                # current dir
                continue
            if name == '..':
                # parent dir
                path, _, _ = path.rpartition(os.path.sep)
                continue
            newpath = path + os.path.sep + name
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
    found.append(_resolve(base, str(path)) or os.path.sep)

    return found


async def _watch_task(path, callback):
    if not os.path.exists(path):
        return

    watcher = Watcher()
    await watcher.setup(asyncio.get_event_loop())

    paths = set()
    try:
        while True:
            old_paths = paths

            # Find all paths related to self.path (resolving symlinks as we go)
            paths = set(_resolve_paths(path))

            # Unwatch old paths
            for old_path in (old_paths - paths):
                logger.debug(f"Unwatching {old_path!r}")
                watcher.unwatch(old_path)

            # Watch new paths
            for new_path in (paths - old_paths):
                logger.debug(f"Watching {new_path!r}")
                watcher.watch(
                    path=new_path,
                    flags=MODIFY_FLAGS,
                )

            # Send notification that change was detected
            callback()

            # Sleep until an event touches one of the paths we care about
            event = await watcher.get_event()

            # We have to rewatch the file that changed because we care about atomic renames
            # Because we are watching a handle, an atomic rename means handle will now point
            # somewhere else entirely and we'll not detect future changes
            logger.debug(f"Detected {event.alias!r} unwatched - rewatching")
            watcher.unwatch(event.alias)
            watcher.watch(
                path=event.alias,
                flags=MODIFY_FLAGS
            )

    finally:
        watcher.close()


def start_watching(path, callback):
    """
    Watch path for changes and call callback when they happen.

    Calls callback() immediately after setting up inotify machinery to ensure it didn't miss a change.

    Attempts to deal with "symlink farms" appropriately.
    """

    if not aionotify:
        logger.warning(f"Changes to {path!r} will not be detected as aionotify is not installed")
        return

    return supervise(_watch_task, path, callback)
