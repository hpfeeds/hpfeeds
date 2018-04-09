# hpfeeds3

[![PyPI](https://img.shields.io/pypi/v/hpfeeds3.svg)](https://pypi.python.org/pypi/hpfeeds3) [![Codecov](https://img.shields.io/codecov/c/github/Jc2k/hpfeeds3.svg)](https://codecov.io/gh/Jc2k/hpfeeds3)


## About

hpfeeds is a lightweight authenticated publish-subscribe protocol. It has a simple wire-format so that everyone is able to subscribe to the feeds with their favorite language in almost no time. Different feeds are separated by channels and support arbitrary binary payloads. This means that the channel users decide the structure of data. It is common to pass JSON over hpfeeds.

This project aims to deliver a modern python 3 compatible broker written on top of asyncio as well as a python 3 compatible client.


## Installation

To use the client you need to install it in your python environment with `pip`.

```
pip install hpfeeds3
```

The core client does not have any dependencies. You can install the broker dependencies with pip too:

```
pip install hpfeeds3[broker]
```

You can also run a broker with Docker:

```
docker run -p "0.0.0.0:20000:20000" -p "0.0.0.0:9431:9431" jc2k/hpfeeds3-broker:latest
```

It will store access keys in an sqlite database in `/app/var`. The `sqlite` client installed in the container for managing access. You should make sure `/app/var` is a volume. Your clients can connect to port `20000`, and prometheus can connect on port `9431`.
