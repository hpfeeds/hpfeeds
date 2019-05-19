# hpfeeds

[![PyPI](https://img.shields.io/pypi/v/hpfeeds.svg)](https://pypi.python.org/pypi/hpfeeds)
[![Codecov](https://img.shields.io/codecov/c/github/hpfeeds/hpfeeds.svg)](https://codecov.io/gh/hpfeeds/hpfeeds)
[![Read the Docs](https://readthedocs.org/projects/hpfeeds/badge/?version=latest)](https://hpfeeds.readthedocs.io/en/latest/?badge=latest)

## About

hpfeeds is a lightweight authenticated publish-subscribe protocol. It has a simple wire-format so that everyone is able to subscribe to the feeds with their favorite language in almost no time. Different feeds are separated by channels and support arbitrary binary payloads. This means that the channel users decide the structure of data. It is common to pass JSON over hpfeeds.

This project aims to deliver a modern python 3 compatible broker written on top of asyncio as well as a python 3 compatible client.

## Installation

The core client does not have any dependencies. You can install it with with `pip`.

```bash
pip install hpfeeds
```

You can run a command line tail of a hpfeeds channel with the command line:

```bash
hpfeeds subscribe --host localhost -p 10000 -i myident -s mysecret -c mychannel
```

You can also publish a single event too:

```bash
hpfeeds publish --host localhost -p 10000 -i myident -s mysecret -c mychannel '{"event": "ping"}'
```

You can install the broker dependencies with pip too:

```bash
pip install hpfeeds[broker]
```

You can also run a broker with Docker:

```
docker run -p "0.0.0.0:20000:20000" -p "0.0.0.0:9431:9431" hpfeeds/hpfeeds-broker:latest
```

It will store access keys in an sqlite database in `/app/var`. The `sqlite` client installed in the container for managing access. You should make sure `/app/var` is a volume. Your clients can connect to port `20000`, and prometheus can connect on port `9431`.

More detailed documentation is available at https://python.hpfeeds.org.
