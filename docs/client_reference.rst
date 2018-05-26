.. _hpfeeds-sync-client-reference:


Client Reference
================

.. module:: hpfeeds3.client
.. currentmodule:: hpfeeds3.client


Client
------

Use the :py:class:`Client` class to perform blocking synchronous operations
against a broker.

.. warning::

   Using this class with `gevent` from multiple greenlets may cause protocol
   stream errors. If using `gevent` you **must** have a publish queue with a
   single greenlet writing to the socket, or take a lock when using `publish`.

   This problem does not exist with asyncio or Twisted.


Usage example::

    import sys
    import hpfeeds


    def main():
        hpc = hpfeeds.new('localhost', 10000, 'ident', 'secret')

        def on_message(identifier, channel, payload):
          print(identifier, payload)

        def on_error(payload):
            print(' -> errormessage from server: {0}'.format(payload), file=sys.stderr)
            hpc.stop()

        hpc.subscribe('cowrie.sessions')
        hpc.run(on_message, on_error)
        hpc.close()
        return 0

    if __name__ == '__main__':
        try: sys.exit(main())
        except KeyboardInterrupt:sys.exit(0)


.. class:: Client(host, port, ident, secret, timeout, reconnect, sleepwait)

 host, port, ident, secret,

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
