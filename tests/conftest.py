import logging
import sys

import pytest

collect_ignore = []
if sys.version_info[0] == 2:
    collect_ignore.extend([
        "tests/test_broker_auth_databases.py",
    ])


@pytest.fixture(autouse=True)
def caplog_defaultloglevel(caplog):
    caplog.set_level(logging.DEBUG)
