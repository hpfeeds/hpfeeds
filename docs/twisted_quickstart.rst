.. _hpfeeds-twisted-client-quickstart:


Twisted Quickstart
==================

.. module:: hpfeeds3.twisted
.. currentmodule:: hpfeeds3.twisted


Most common tasks you'll need to perform in Twisted against a hpfeeds broker
can be accomplished with an instance of :class:`ClientSessionService`.

This class implements :py:class:`twisted.application.service.IService`. In the
most basic cases you can manually call ``startService`` and ``stopService``::

    from twisted.internet.task import react
    from hpfeeds.twisted import ClientSessionService


    @defer.inlineCallbacks
    def main():
        client = ClientSessionService('localhost', 20000, 'ident', 'secret')

        # Start trying to connect to a broker
        client.startService()

        # Suspend execution of main until connection established
        yield client.whenConnected

        # Use API
        client.publish('...', b'...')

        # Disconnect from broker - pause execution of main() until disconnect completed
        yield client.stopService()


    if __name__ == '__main__':
        react(main())


If your application is using the ``IService`` interface already then you might
be able to use ``setServiceParent`` to attach this client to one of your
existing components. For in a ``.tac`` file you could::


    from twisted.application import service
    from hpfeeds.twisted import ClientSessionService

    application = service.Application('my-application')

    client = ClientSessionService('localhost', 20000, 'ident', 'secret')
    client.setServiceParent(application)

Now whenever any existing machinery calls ``startService`` or ``stopService``
then client connection will be automatically started or stopped as well.

If you are running on Python 3 you also have the option of using ``async with``.
This is great for short lived connections or simple pipelines::

    from twisted.internet.defer import ensureDeferred
    from twisted.internet.task import react
    from hpfeeds.twisted import ClientSessionService


    async def main():
        async with ClientSessionService('localhost', 20000, 'ident', 'secret') as client:
            # Use API
            client.publish('...', b'....')


    if __name__ == '__main__':
        react(ensureDeferred(main()))


Publishing an event
-------------------

Here is the simplest example of sending an event (in that it doesn't use Python
3 specific features or Twisted's IService)::

    from twisted.internet.task import react
    from hpfeeds.twisted import ClientSessionService


    @defer.inlineCallbacks
    def main():
        client = ClientSessionService('localhost', 20000, 'ident', 'secret')
        client.startService()
        yield client.whenConnected

        client.publish('channel', b'{"data": "fefefefefefef"}')

        yield client.stopService()

    react(main())


See the introduction for simpler ways of starting a client, depending on your
needs.


Listening to events
-------------------

Here is the simplest example of sending an event (in that it doesn't use Python
3 specific features or Twisted's IService)::

    from twisted.internet.task import react
    from hpfeeds.twisted import ClientSessionService


    @defer.inlineCallbacks
    def main():
        client = ClientSessionService('localhost', 20000, 'ident', 'secret')
        client.startService()
        yield client.whenConnected

        while True:
            ident, channel, payload = yield client.read()
            print(payload)

        yield client.stopService()

    react(main())

If you are on Python 3 you can use ``async for``::

    from twisted.internet.defer import ensureDeferred
    from twisted.internet.task import react
    from hpfeeds.twisted import ClientSessionService


    @defer.inlineCallbacks
    def main():
        with ClientSessionService('localhost', 20000, 'ident', 'secret') as client:
            client.subscribe('test-channel')
            for ident, channel, payload in client:
                print(payload)


    react(ensureDeferred(main()))
