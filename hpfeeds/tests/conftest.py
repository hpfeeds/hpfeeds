import logging

import pytest


@pytest.fixture(autouse=True)
def caplog_defaultloglevel(caplog):
    caplog.set_level(logging.DEBUG)
