from prometheus_client import Counter, Gauge, Histogram

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
