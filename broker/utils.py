#!/usr/bin/python
# -*- coding: utf8 -*-

import logging
import logging.handlers
import hashlib

import config

# custom exception classes
class Disconnect(Exception):
	pass

class BadClient(Exception):
	pass

def hash(a, b):
	return hashlib.sha1('{0}{1}'.format(a, b)).digest()
