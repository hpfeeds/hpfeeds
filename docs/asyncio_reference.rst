.. _hpfeeds-asyncio-client-reference:


Client Reference
================

.. module:: hpfeeds3.asyncio
.. currentmodule:: hpfeeds3.asyncio


Client Session
--------------

Client session is the recommended interface for subscribing and publish to a
hpfeeds broker with asyncio.


Usage example::

    import asyncio
    from hpfeeds.asyncio import ClientSession


    async def main():
        async with ClientSession('localhost', 20000, 'ident', 'secret') as client:
            client.publish('channel', b'{"data": "fefefefefefef"}')


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


.. class:: ClientSession(host, port, ident, secret)

   The class for creating client sessions and publish/subscribing.

   Instances of this class will automatically maintain a connection to the
   broker and try to reconnect if that connection fails.

   :param str host: The broker to connect to.

   :param str port: The port to connect to.

   :param str ident: The identity to authenticate with.

   :param str secret: The secret to authenticat with.


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
