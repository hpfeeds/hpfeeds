.. _hpfeeds-asyncio-client-quickstart:


Client Quickstart
=================

.. module:: hpfeeds3.asyncio
.. currentmodule:: hpfeeds3.asyncio


Most common tasks you'll need to perform in asyncio against a hpfeeds broker
can be accomplished with an instance of :class:`ClientSession`.


Publishing an event
-------------------

Usage example::

    import asyncio
    from hpfeeds.asyncio import ClientSession


    async def main():
        async with ClientSession('localhost', 20000, 'ident', 'secret') as client:
            client.publish('channel', b'{"data": "fefefefefefef"}')


    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())


Listening to events
-------------------

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


Publishing events from an asynchronous iterator
-----------------------------------------------

You can now construct asynchronous generators in Python 3, and then have
hpfeeds3 publish directly from the iterator::

    import asyncio

    async def test_iterator():
        while True:
            wait asyncio.sleep(1)
            yield b'payload'

    async def main():
        async with ClientSession('localhost', 20000, 'ident', 'secret') as client:
            client.publish_async_iterable('channel', test_iterator())


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
