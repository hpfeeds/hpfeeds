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


async def metrics(request):
    data = generate_latest(REGISTRY)
    return web.Response(text=data.decode('utf-8'), content_type='text/plain', charset='utf-8')


async def start_metrics_server(host, port):
    app = web.Application()
    app.router.add_get('/metrics', metrics)

    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)

    await site.start()

    return runner
