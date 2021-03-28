import sys


collect_ignore = []
if sys.version_info[0] == 2:
    collect_ignore.extend([
        "tests/test_asyncio_client.py",
        "tests/test_asyncio_protocol.py",
        "tests/test_broker_connection.py",
        "tests/test_broker_prometheus.py",
        "tests/test_client_integration.py",
        "tests/test_twisted_service.py",
        "tests/test_broker_auth_env.py",
        "tests/test_broker_auth_sqlite.py",
        "tests/test_broker_auth_databases.py",
    ])

