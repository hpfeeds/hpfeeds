.. _hpfeeds-twisted-client-reference:


Client Reference
================

.. module:: hpfeeds3.twisted
.. currentmodule:: hpfeeds3.twisted


Client Session
--------------

ClientSessionService is the recommended interface for subscribing and publish to
a hpfeeds broker with Twisted.

.. class:: ClientSessionService(endpoint, ident, secret)

   :param str endpoint: A Twisted endpoint describing the broker to connect to.

   :param str ident: The identity to authenticate with.

   :param str secret: The secret to authenticate with.

   The class for creating client sessions and publish/subscribing.

   Instances of this class will automatically maintain a connection to the
   broker and try to reconnect if that connection fails.

  .. method:: read()

      Retrieve a single message from the broker.

      :return: A `Deferred` that fires on delivery of a message by the broker.
      :rtype: twisted.internet.defer.Deferred

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
