Welcome to hpfeeds3
===================

hpfeeds client and server for Python.

Key Features
============

 * Async non-blocking asyncio-powered broker
 * Supports asyncio
 * Supports Twisted


.. _hpfeeds-installation:


Running a broker
================

The simplest way to run a broker is with our official Docker image:

.. code-block:: bash

   $ docker run -p "0.0.0.0:20000:20000" -p "0.0.0.0:9431:9431" jc2k/hpfeeds3-broker:latest


Library Installation
====================

.. code-block:: bash

   $ pip install hpfeeds3

If you are planning to install a broker you can install the extra broker
dependencies:

.. code-block:: bash

   $ pip install hpfeeds3[broker]


.. _hpfeeds-source:


Source code
===========

The project is hosted on GitHub_

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
