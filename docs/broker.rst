Hpfeeds Broker
==============

The core service in any hpfeeds based service is its broker. Data is collected
remotely and published to a channel on the broker. All subscribers to that
channel then receive a copy.


Getting started
===============

The easiest way to get started with the broker is with Docker. You can run one
as easily as:

.. code-block:: bash

   $ docker run \
       -p "0.0.0.0:10000:10000" \
       jc2k/hpfeeds3-broker:latest

This will start a broker that is listening for publishers and subscribers on
port 10000.

It is much more maintainable to use a `docker-compose.yml`:

.. code-block:: yaml

   version: '2.1'

   services:
     hpfeeds:
       image: jc2k/hpfeeds3-broker
       container_name: hpfeeds
       ports:
        - "0.0.0.0:10000:10000"

You can start this with:

.. code-block:: bash

   $ docker-compose up -d

And stop it with

.. code-block:: bash

   $ docker-compose down

You can also install the python package directly:

.. code-block:: bash

   $ pip install hpfeeds3[broker]

You can then run it in the foreground with:

.. code-block:: bash

   $ hpfeeds-broker --bind 0.0.0.0:10000 --name mybroker


Authentication
==============

The default authentication backend is sqlite. If you are using this backend
then you should make sure your broker container has a volume to store the db:

.. code-block:: yaml

   version: '2.1'

   volumes:
     hpfeeds_userdb: {}

   services:
     hpfeeds:
       image: jc2k/hpfeeds3-broker
       container_name: hpfeeds
       ports:
        - "0.0.0.0:10000:10000"
       volumes:
        - hpfeeds_data:/app/var

Unfortunately managing access keys currently involves SQL! You can use
docker-compose to get an sqlite shell:

.. code-block:: bash

   $ docker-compose run --rm hpfeeds sqlite3 sqlite.db

You can list users with

.. code-block:: sql

    SELECT * FROM authkeys;

You can insert users with:

.. code-block:: sql

    INSERT INTO authkeys (owner, ident, secret, pubchans, subchans)
        VALUES ('owner', 'ident', 'secret', '["chan1"]', '["chan1"]');

You don't need to restart the broker.


Test authentication
===================

When you are adding hpfeeds to a project you often want a test broker. You
want to test authentication, but you don't care about being able to add/remove
users at runtime.

The broker ships with an `env` auth backend that reads from the environment.

If you wanted to add an `ident` of `james` and a `secret` of `password` that can
subscribe to `test-chan` then you would set the following environment variables:

.. code-block:: bash

    export HPFEEDS_JAMES_SECRET=secret
    export HPFEEDS_JAMES_SUBCHANS=test-chan

You can set these variables in your `docker-compose.yml`:

.. code-block:: yaml

   version: '2.1'

   services:
     hpfeeds:
       image: jc2k/hpfeeds3-broker
       environment:
         HPFEEDS_TEST_SECRET: 'test'
         HPFEEDS_TEST_SUBCHANS: 'spam'
         HPFEEDS_TEST_PUBCHANS: 'spam'
       command:
        - '/app/bin/hpfeeds-broker'
        - '--bind=0.0.0.0:10000'
        - '--auth=env'
       ports:
        - "0.0.0.0:10000:10000"


TLS Authentication
==================

You can use a self-signed certificate:

.. code-block:: bash

    $ openssl req -x509 -newkey rsa:2048 -keyout broker.key -nodes \
        -out broker.crt -sha256 -days 1000

You can start the broker using this cert with::

    $  hpfeeds-broker --bind=0.0.0.0:10000 --tlskey=broker.key --tlscert=broker.crt

Or if using docker-compose::

.. code-block:: yaml

   version: '2.1'

   volumes:
     hpfeeds_userdb: {}

   services:
     hpfeeds:
       image: jc2k/hpfeeds3-broker
       container_name: hpfeeds
       ports:
        - "0.0.0.0:10000:10000"
       volumes:
        - hpfeeds_data:/app/var
       command:
        - '/app/bin/hpfeeds-broker'
        - '--bind=0.0.0.0:10000'
        - '--tlskey=broker.key'
        - '--tlscert=broker.crt'


Monitoring
==========

The broker has built in support for Prometheus monitoring. It can listen on
port `9431` (or a port of your choosing) and answer to HTTP requests for
`/metrics`.

Once these are captured by Prometheus you can use Grafana to create dashboards
showing number of active connections, number of active subscribers (per channel)
and events per second. You can also see connect rates and error rates.

Metrics are turned on by default in the official Docker image, you just need to
expose the port:

.. code-block:: yaml

    version: '2.1'

    volumes:
      hpfeeds_userdb: {}

    services:
      hpfeeds:
        image: jc2k/hpfeeds3-broker
        container_name: hpfeeds
        ports:
         - "0.0.0.0:10000:10000"
         - "127.0.0.1:9431:9431"
        volumes:
         - hpfeeds_data:/app/var

If you are overriding the command line, the setting that controls the port is `--exporter`:

.. code-block:: yaml

   version: '2.1'

   services:
     hpfeeds:
       image: jc2k/hpfeeds3-broker
       environment:
         HPFEEDS_TEST_SECRET: 'test'
         HPFEEDS_TEST_SUBCHANS: 'spam'
         HPFEEDS_TEST_PUBCHANS: 'spam'
       command:
        - '/app/bin/hpfeeds-broker'
        - '--bind=0.0.0.0:10000'
        - '--exporter=0.0.0.0:9431'
        - '--auth=env'
       ports:
        - "0.0.0.0:10000:10000"
        - "127.0.0.1:9431:9431"
