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


    async def main():
        async with ClientSessionService('localhost', 20000, 'ident', 'secret') as client:
            client.publish('channel', b'{"data": "fefefefefefef"}')


    react(ensureDeferred(main()))


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
