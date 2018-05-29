.. _hpfeeds-sync-client-reference:


Client Reference
================

.. module:: hpfeeds3.client
.. currentmodule:: hpfeeds3.client


.. class:: Client(host, port, ident, secret, timeout, reconnect, sleepwait)

   The class for creating client sessions and publish/subscribing.

   Instances of this class will automatically maintain a connection to the
   broker and try to reconnect if that connection fails.

   :param str host: The broker to connect to.

   :param str port: The port to connect to.

   :param str ident: The identity to authenticate with.

   :param str secret: The secret to authenticate with.

   :param timeout:

   :param reconnect: Whether or not the client should reconnect.

   :param sleepwait:

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
