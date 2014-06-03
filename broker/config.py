#!/usr/bin/python
# -*- coding: utf8 -*-

# debug, turns on debug logging output
DEBUG = True

# bind to this
FBIP = "0.0.0.0"

# listen port
FBPORT = 20000

# name (OP_INFO)
FBNAME = "hpfriends"

# SSL options ({} makes plain socket)
SSLOPTS = {}
SSLOPTS = dict(keyfile="./server.key", certfile="./server.crt")

# database addr
DBPATH = "db.sqlite3"

# how often to save connection stats
STAT_TIME = 60.0
