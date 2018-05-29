.. _hpfeeds-sync-client-reference:


Client Quickstart
=================

.. module:: hpfeeds3.client
.. currentmodule:: hpfeeds3.client


Use the :py:class:`Client` class to perform blocking synchronous operations
against a broker. If you aren't using Twisted or asyncio, then this is probably
the client you are looking for.

To create a new client you can use the ``new`` function in the main ``hpfeeds``
module::

    client = hpfeeds.new('localhost', 10000, 'ident', 'secret')

If you want to turn on TLS support you need to specify a path to a public
certificate::

    client = hpfeeds.new(
        'localhost',
        10000,
        'ident',
        'secret',
        certfile='path/to/certificate.pem',
    )

If you want to turn off automatic reconnects you can::

    client = hpfeeds.new(
        'localhost',
        10000,
        'ident',
        'secret',
        reconnect=False,
    )


Sending events
--------------

.. warning::

   Using this class with `gevent` from multiple greenlets may cause protocol
   stream errors. If using `gevent` you **must** have a publish queue with a
   single greenlet writing to the socket, or take a lock when using `publish`.

   This problem does not exist with asyncio or Twisted.


You can use the ``publish`` method to publish data to broker::

   import hpfeeds


   def main():
       client = hpfeeds.new('localhost', 10000, 'ident', 'secret')
       client.publish('channel', b'payload')
       client.close()


Listening to events from the broker
-----------------------------------

You can subscribe to a channel on the broker and then give the client callbacks
to call when something happens::

    import hpfeeds


    def on_message(identifier, channel, payload):
        print(identifier, payload)


    def on_error(payload):
        print(' -> errormessage from server: {0}'.format(payload), file=sys.stderr)
        hpc.stop()


    def main():
        hpc = hpfeeds.new('localhost', 10000, 'ident', 'secret')

        hpc.subscribe('cowrie.sessions')
        hpc.run(on_message, on_error)
        hpc.close()
