Client Reference
================

This library contains 3 implementations of hpfeeds client. All are shipped in
the ``hpfeeds3`` wheel and can be installed with pip:

.. code-block:: bash

   $ pip install hpfeeds3


Blocking client
---------------

A simple blocking client that handles reconnecting and authentication.
Compatible with Python 2.7 and alter.

 * :doc:`Quick Start <client_quickstart>`
 * :doc:`Client reference <client_reference>`


asyncio
-------

Compatible with Python 3.6 and later, we ship a non blocking client that builds
on the asyncio framework that is now part of the Python 3 standard library.

* :doc:`Quick Start <asyncio_quickstart>`
* :doc:`Client reference <asyncio_reference>`


Twisted
-------

Compatible with Python 2.7 and later, with support for the new coroutine
features in Python 3, we also have a Twisted Service that makes it easy to
integrate hpfeeds into your codebase.

* :doc:`Quick Start <twisted_reference>`
* :doc:`Client reference <twisted_reference>`
