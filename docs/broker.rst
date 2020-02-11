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
       hpfeeds/hpfeeds-broker:latest

This will start a broker that is listening for publishers and subscribers on
port 10000.

It is much more maintainable to use a `docker-compose.yml`:

.. code-block:: yaml

   version: '2.1'

   services:
     hpfeeds:
       image: hpfeeds/hpfeeds-broker
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

   $ pip install hpfeeds[broker]

You can then run it in the foreground with:

.. code-block:: bash

   $ hpfeeds-broker -e tcp:port=10000 --name mybroker


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
       image: hpfeeds/hpfeeds-broker
       container_name: hpfeeds
       ports:
        - "0.0.0.0:10000:10000"
       volumes:
        - hpfeeds_userdb:/app/var

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


JSON authentication store
=========================

When starting the broker you can pass with path to a `.json` file. It will then load all the users
in that file. For example:

```bash
hpfeeds-broker -e tcp:port=20000 --exporter=0.0.0.0:9431 --auth=/var/lib/hpfeeds/users.json
```

The accounts must be formatted as a mapping where the ident is the key:

```json
{
  "my-user-ident": {
    "owner": "my-owner",
    "secret": "my-really-strong-passphrase",
    "subchans": ["chan1"],
    "pubchans": [],
  }
}
```

If the `aionotify` package is installed and the host os is Linux then the broker will automatically
reload the JSON file when it opens.

This is handy where you have a small number of user accounts and you already have infrastructure
orchestration that can easily replicate a password file. For example, when using Kubernetes and
its secret type updates to the secret object in the Kubernetes API will be automatically synced to
a Pod's filesystem. Hpfeeds will spot those updates and process them immediately without needing a
restart.


Mongo authentication store
=========================

When starting the broker you can pass a mongo connection string. Auth requests are then checked against
the selected Database in a collection named auth_keys. Any authentication can be included within the connection string
For example:

```bash
hpfeeds-broker -e tcp:port=20000 --exporter=0.0.0.0:9431 --auth="mongodb://127.0.0.1:27017/hpfeeds"
```

```bash
hpfeeds-broker -e tcp:port=20000 --exporter=0.0.0.0:9431 --auth="mongodb://admin:admin@127.0.0.1:27017/hpfeeds"
```

An example Mongo Document:

```json
{
  "identifier": "testing",
  "secret": "secretkey",
  "publish": [ "chan1","chan2"],
  "subscribe": ["chan2"]
}
```

To Find all users

```bash
mongo
> use hpfeeds
switched to db hpfeeds
> show collections
auth_key
> db.auth_key.find()
{ "_id" : ObjectId("5e35e5f09ba2a06adeef5be0"), "identifier" : "49be3430-4535-11ea-90b0-0242ac140004", "secret" : "q8JeUC043OYs7Mmz", "publish" : [ ], "subscribe" : [ ] }
> 
```

To add a new user

```bash
mongo -u admin -padmid
> use hpfeeds
switched to db hpfeeds
> db.auth_key.insert({"identifier": "testing", "secret": "secretkey", "publish": ["chan1", "chan2"], subscribe: ["chan2"]})
WriteResult({ "nInserted" : 1 })
> 
```


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
       image: hpfeeds/hpfeeds-broker
       environment:
         HPFEEDS_TEST_SECRET: 'test'
         HPFEEDS_TEST_SUBCHANS: 'spam'
         HPFEEDS_TEST_PUBCHANS: 'spam'
       command:
        - '/app/bin/hpfeeds-broker'
        - '--endpoint=tcp:port=10000'
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

    $  hpfeeds-broker --endpoint=tls:port=10000:key=broker.key:cert=broker.crt

Or if using docker-compose::

.. code-block:: yaml

   version: '2.1'

   volumes:
     hpfeeds_userdb: {}

   services:
     hpfeeds:
       image: hpfeeds/hpfeeds-broker
       container_name: hpfeeds
       ports:
        - "0.0.0.0:10000:10000"
       volumes:
        - hpfeeds_userdb:/app/var
       command:
        - '/app/bin/hpfeeds-broker'
        - '--endpoint=tls:port=10000:key=broker.key:cert=broker.crt'


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
        image: hpfeeds/hpfeeds-broker
        container_name: hpfeeds
        ports:
         - "0.0.0.0:10000:10000"
         - "127.0.0.1:9431:9431"
        volumes:
         - hpfeeds_userdb:/app/var

If you are overriding the command line, the setting that controls the port is `--exporter`:

.. code-block:: yaml

   version: '2.1'

   services:
     hpfeeds:
       image: hpfeeds/hpfeeds-broker
       environment:
         HPFEEDS_TEST_SECRET: 'test'
         HPFEEDS_TEST_SUBCHANS: 'spam'
         HPFEEDS_TEST_PUBCHANS: 'spam'
       command:
        - '/app/bin/hpfeeds-broker'
        - '--endpoint=tcp:port=10000'
        - '--exporter=0.0.0.0:9431'
        - '--auth=env'
       ports:
        - "0.0.0.0:10000:10000"
        - "127.0.0.1:9431:9431"


Multiple interfaces
===================

You can listen on multiple endpoints at once. This is useful if you have some components locally and some remotely and need to differentiate between them. For example::

    $  hpfeeds-broker --endpoint=tls:port=10000:key=broker.key:cert=broker.crt --endpoint=tcp:port=20000:device=lan0

This will allow TLS connections on any interface, and allow plain text connections only via the `lan0` NIC.

The same config with docker-compose::

.. code-block:: yaml

   version: '2.1'

   volumes:
     hpfeeds_userdb: {}

   services:
     hpfeeds:
       image: hpfeeds/hpfeeds-broker
       container_name: hpfeeds
       ports:
        - "0.0.0.0:10000:10000"
       volumes:
        - hpfeeds_userdb:/app/var
       command:
        - '/app/bin/hpfeeds-broker'
        - '--endpoint=tls:port=10000:key=broker.key:cert=broker.crt'
        - '--endpoint=tcp:port=20000:device=lan0'
