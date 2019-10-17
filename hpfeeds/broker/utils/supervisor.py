import asyncio
import logging

logger = logging.getLogger(__name__)


def supervise(callable, *args, **kwargs):
    """
    A supervisor that automatically restarts a long running coroutine if it fails.
    """
    async def _task():
        while True:
            try:
                await callable(*args, **kwargs)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception(f"Supervised task {callable!r} failed and will be restarted")
            await asyncio.sleep(1)

    task = asyncio.ensure_future(_task())

    async def close():
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    return close
