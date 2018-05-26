Welcome to hpfeeds3
===================

hpfeeds is a lightweight authenticated publish-subscribe protocol that supports arbitrary binary payloads. hpfeeds3 is a library containing python 2 +3 implementations, as well as asyncio and Twisted implementations. It also contains a modern asyncio powered broker.


Key Features
============

 * Async non-blocking asyncio-powered broker
 * Supports asyncio
 * Supports Twisted


.. _hpfeeds-installation:


Running a broker
================

Every deployment of hpfeeds needs at least one broker. All messages are
published to the broker and it passes it to the relevant subscribers.

 * :doc:`broker`

You may also be interested in Tentacool, a C++ implementation of a hpfeeds
broker.


Library Installation
====================

.. code-block:: bash

   $ pip install hpfeeds3

If you are planning to install a broker you can install the extra broker
dependencies:

.. code-block:: bash

   $ pip install hpfeeds3[broker]


asyncio
=======

If you are using Python 3.6+ and starting a new project then asyncio might be
the way to go. We ship a non blocking asyncio implementation of our hpfeeds out
of the box.

* :doc:`Client reference <asyncio_reference>`


Twisted
=======

Twisted is a python 2 and 3 compatible asynchronous networking framework. It's
mature and takes a lot of pain out of building robust services. We ship a native
Twisted implementation of hpfeeds out of the box, with no additional
dependencies beyond Twisted itself.

* :doc:`Client reference <twisted_reference>`


Synchronous client
==================

The synchronous client is great for prototyping new subscribers and publishers.
It has no external dependencies.

 * :doc:`Client reference <client_reference>`


.. _hpfeeds-source:

Source code
===========

The project is hosted on `GitHub <https://github.com/Jc2k/hpfeeds3>`_.

Please feel free to file an issue on the `bug tracker
<https://github.com/Jc2k/hpfeeds3/issues>`_ if you have found a bug
or have some suggestion in order to improve the library.

The library uses `Travis <https://travis-ci.com/Jc2k/hpfeeds3>`_ for
Continuous Integration.


.. toctree::
   :maxdepth: 2
   :caption: Contents:



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
