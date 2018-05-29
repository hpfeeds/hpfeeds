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


Writing a simple subscriber for asyncio
---------------------------------------

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


Using hpfeeds with aiostream
----------------------------

aiostream is like an asynchronous version of `itertools`.

For example, you could merge together the output from multiple brokers, perform
transformations on it and send it into another::

     import asyncio

     from asyncio.stream import iterable, merge
     from hpfeeds.asyncio import ClientSession

     async def main():
         brokers = []
         for port in (10000, 10001, 10002):
             session = ClientSession('localhost', 10000, 'ident', 'secret')
             session.subscribe('in-channel')
             brokers.append(session)

         pipeline = (
             # Merge feed from multiple brokers
             merge(*brokers) |

             # Decode JSON payload
             map(lambda ident, channel, payload: json.loads(payload.decode('utf-8'))) |

             # Only interested in events that have hashes associated with them
             filter(lambda payload: len(payload['hashes']) > 0) |

             # Reencode payload for transmission
             map(lambda payload: json.dumps(payload).encode('utf-8'))
         )

         output = ClientSession('localhost', 10004, 'ident', 'secret')
         await output.publish_async_iterable('out-channel', combined)

     loop = asyncio.get_event_loop()
     loop.run_until_complete(main())
