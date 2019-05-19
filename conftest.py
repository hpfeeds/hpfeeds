import sys


collect_ignore = []
if sys.version_info[0] == 2:
    collect_ignore.extend([
        "hpfeeds/tests/test_asyncio_client.py",
        "hpfeeds/tests/test_asyncio_protocol.py",
        "hpfeeds/tests/test_broker_connection.py",
        "hpfeeds/tests/test_broker_prometheus.py",
        "hpfeeds/tests/test_client_integration.py",
        "hpfeeds/tests/test_twisted_service.py",
    ])

