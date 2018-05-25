from aiohttp import web
from prometheus_client import (
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

CLIENT_CONNECTIONS = Gauge(
    'hpfeeds_broker_client_connections',
    'Number of clients connected to broker',
)

CONNECTION_MADE = Counter(
    'hpfeeds_broker_connection_made',
    'Number of connections established',
)

CONNECTION_READY = Counter(
    'hpfeeds_broker_connection_ready',
    'Number of connections established + authenticated',
    ['ident'],
)

CONNECTION_ERROR = Counter(
    'hpfeeds_broker_connection_error',
    'Number of connections that experienced a protocol error',
    ['ident', 'category'],
)

CONNECTION_LOST = Counter(
    'hpfeeds_broker_connection_lost',
    'Number of connections lost',
    ['ident'],
)

SUBSCRIPTIONS = Gauge(
    'hpfeeds_broker_subscriptions',
    'Number of subscriptions to a channel',
    ['ident', 'chan'],
)

RECEIVE_PUBLISH_COUNT = Counter(
    'hpfeeds_broker_receive_publish_count',
    'Number of events received by broker for a channel',
    ['ident', 'chan'],
)

RECEIVE_PUBLISH_SIZE = Histogram(
    'hpfeeds_broker_receive_publish_size',
    'Sizes of messages received by broker for a channel',
    ['ident', 'chan'],
)


def reset():
    ''' Reset the metrics to 0. This is intended for tests **only**. '''
    CLIENT_CONNECTIONS._value.set(0)
    SUBSCRIPTIONS._metrics = {}
    RECEIVE_PUBLISH_SIZE._metrics = {}
    RECEIVE_PUBLISH_COUNT._metrics = {}
    CONNECTION_ERROR._metrics = {}
    CONNECTION_LOST._metrics = {}
    CONNECTION_MADE._value.set(0)
    CONNECTION_READY._metrics = {}


async def metrics(request):
    data = generate_latest(REGISTRY)
    return web.Response(text=data.decode('utf-8'), content_type='text/plain', charset='utf-8')


async def start_metrics_server(host, port):
    app = web.Application()
    app.router.add_get('/metrics', metrics)

    runner = web.AppRunner(app, access_log=None)
    await runner.setup()

    site = web.TCPSite(runner, host, port)

    await site.start()

    return runner
