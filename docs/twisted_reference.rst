.. _hpfeeds-twisted-client-reference:


Client Reference
================

.. module:: hpfeeds3.twisted
.. currentmodule:: hpfeeds3.twisted


Client Session
--------------

ClientSessionService is the recommended interface for subscribing and publish to
a hpfeeds broker with Twisted.


Usage example::

    from twisted.internet.defer import ensureDeferred
    from twisted.internet.task import react
    from hpfeeds.twisted import ClientSessionService


    @defer.inlineCallbacks
    def main():
        service = ClientSessionService('localhost', 20000, 'ident', 'secret') as client:
        service.startService()
        yield service.whenConnected

        service.publish('channel', b'{"data": "fefefefefefef"}')

        yield service.stopService()

    react(ensureDeferred(main()))

See below for an example of how Python 3 syntax sugar makes much much nicer.


.. class:: ClientSessionService(endpoint, ident, secret)

   The class for creating client sessions and publish/subscribing.

   Instances of this class will automatically maintain a connection to the
   broker and try to reconnect if that connection fails.

   :param str endpoint: A Twisted endpoint describing the broker to connect to.

   :param str ident: The identity to authenticate with.

   :param str secret: The secret to authenticate with.


   .. comethod:: read()

      :coroutine:

      Returns a message received by the broker. It's future will not fire until
      a message is available.

  .. method:: publish(channel, payload)

     :param str channel: The channel to post the payload to.

     :param bytes payload: The data to publish to the broker.

     Send the given payload to the given channel.

  .. method:: subscribe(channel)

     :param str channel: The channel to subscribe to.

     Subscribe to the named channel.

  .. method:: unsubscribe(channel)

     :param str channel: The channel to subscribe to.

     Unsubscribe from the named channel.


Writing a simple subscriber
---------------------------

You can just async for over your client to read from the broker forever::

   import asyncio
   from hpfeeds.asyncio import ClientSession


   async def main():
       async with ClientSession('localhost', 20000, 'ident', 'secret') as client:
           client.subscribe('channel')

           async for ident, channel, payload in client:
               print(payload)


   loop = asyncio.get_event_loop()
   loop.run_until_complete(main())


Twisted and Python 3
--------------------

If your Python is new enough you can take advantage of coroutines with this
client.

For example publishing to a broker is now simply::

    from twisted.internet.defer import ensureDeferred
    from twisted.internet.task import react
    from hpfeeds.twisted import ClientSessionService


    async def main():
        async with ClientSessionService('localhost', 20000, 'ident', 'secret') as client:
            client.publish('channel', b'{"data": "fefefefefefef"}')


    react(ensureDeferred(main()))

And a simple subscriber now looks like this::

    from twisted.internet.defer import ensureDeferred
    from twisted.internet.task import react
    from hpfeeds.twisted import ClientSessionService


    async def main():
        async with ClientSessionService('localhost', 20000, 'ident', 'secret') as client:
            client.subscribe('channel')

            async for ident, chan, payload in client:
                print(payload)


    react(ensureDeferred(main()))
