Command line reference
======================

All commands are against a broker, and you need to provider the broker details
on the command line:

.. code-block:: bash

    $ hpfeeds subscribe --host localhost -p 10000 -i myident -s mysecret -c mychannel

If connecting to a TLS enabled broker you can enable TLS mode by passing a public
certificate for the broker to the CLI.

.. code-block:: bash

    $ hpfeeds <action> --tlscert mycert.crt --host localhost -p 10000 -i myident -s mysecret -c mychannel

If you are having trouble connecting to the broker you can use the ``--debug``
option to see more verbose output.


Subscribing
-----------

You can subscribe to a broker with:

.. code-block:: bash

    $ hpfeeds subscribe --host localhost -p 10000 -i myident -s mysecret -c mychannel

You can specify multiple channels. You will see messages live as they arrive
from the broker.

Ctrl+C to exit the stream.


Publish from command line
-------------------------

You can send a single event using the hpfeeds client.

.. warning::

    This approach will establish a connection for every event and should not be
    used for high volume data.

.. code-block:: bash

    $ hpfeeds publish --host localhost -p 10000 -i myident -s mysecret -c mychannel '{"event": "ping"}'


Publish from a file
-------------------

You can send the contents of a file as a single event.

.. warning::

    This approach will establish a connection for every event and should not be
    used for high volume data.

.. code-block:: bash

    $ hpfeeds publish --host localhost -p 10000 -i myident -s mysecret -c mychannel path/to/malware.bin.
