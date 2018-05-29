Welcome to hpfeeds3
===================

hpfeeds is a lightweight authenticated publish-subscribe protocol that supports arbitrary binary payloads. It is designed to be simple to implement and thus programming language agnostic. hpfeeds3 is a library containing python 2 +3 implementations, as well as asyncio and Twisted implementations. 

It also contains a modern asyncio powered broker with integrated Prometheus monitoring.


Running a broker
----------------

Every deployment of hpfeeds needs at least one broker. All messages are
published to the broker and it passes it to the relevant subscribers.

 * :doc:`broker`

You may also be interested in Tentacool, a C++ implementation of a hpfeeds
broker.


Command line client
-------------------

We ship with a simple command line that can subscribe to a broker or publish it.
See :doc:`command line reference <cli>`.


Implementor guidelines
----------------------

If you are adding hpfeeds to a project we've collected together a few tips :doc:`here <implementors>`.


Client reference
----------------

If you want to use hpfeeds with Python then see our :doc:`client reference guides <clients>`.


Developers
----------

If you want to add hpfeeds to a non-Python application or you want to understand
what is happening underneath this library you may be interested in the
:doc:`Protocol reference <protocol>`.


Source code
-----------

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
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
