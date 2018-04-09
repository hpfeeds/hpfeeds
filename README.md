# hpfeeds3

[![PyPI](https://img.shields.io/pypi/v/hpfeeds3.svg)](https://pypi.python.org/pypi/hpfeeds3) [![Codecov](https://img.shields.io/codecov/c/github/Jc2k/hpfeeds3.svg)](https://codecov.io/gh/Jc2k/hpfeeds3)


## About

hpfeeds is a lightweight authenticated publish-subscribe protocol. It has a simple wire-format so that everyone is able to subscribe to the feeds with their favorite language in almost no time. Different feeds are separated by channels and support arbitrary binary payloads. This means that the channel users decide the structure of data. It is common to pass JSON over hpfeeds.

This project aims to deliver a modern python 3 compatible broker written on top of asyncio as well as a python 3 compatible client.


## Installation

```
pip install hpfeeds3
```
