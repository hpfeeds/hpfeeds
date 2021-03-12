Hpfeeds Broker
==============

The core service in any hpfeeds based service is its broker. Data is collected
remotely and published to a channel on the broker. All subscribers to that
channel then receive a copy.

If you are running the broker outside of Docker please not that Windows is not supported and you must be using Python 3.6 or later.

The examples below assume support for docker-compose 2.1 files or later. hpfeeds should still work if you have an older environment, but you will need to write your own docker-compose configuration for your older docker-compose installation.


Super-easy throwaway test broker
================================

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

And start a broker with `docker-compose up`.


Authentication
==============

For a more long lived broker you want to use more than environment variables for your authentication. There are a couple of options.

JSON authentication store
-------------------------

When starting the broker you can pass with path to a `.json` file. It will then load all the users
in that file. For example:

```bash
hpfeeds-broker -e tcp:port=20000 --exporter=0.0.0.0:9431 --auth=/var/lib/hpfeeds/users.json
```

The accounts must be formatted as a mapping where the ident is the key:

.. code-block:: json

    {
      "my-user-ident": {
        "owner": "my-owner",
        "secret": "my-really-strong-passphrase",
        "subchans": ["chan1"],
        "pubchans": [],
      }
    }


If the `aionotify` package is installed and the host os is Linux then the broker will automatically
reload the JSON file whenever it changes.

This is handy where you have a small number of user accounts and you already have infrastructure
orchestration that can easily replicate a password file. For example, when using Kubernetes and
its secret type updates to the secret object in the Kubernetes API will be automatically synced to
a Pod's filesystem. Hpfeeds will spot those updates and process them immediately without needing a
restart.

Database authentication store
--------------------------

Please note that this authentication provider is only supported when running with `Python >= 3.5`
If you need to use an SQLite auth provider and you are not able to install the database dependancies as listed below
you will need to use the default SQLite provider. 

When starting the broker you can pass a database connection string. Auth requests are then checked against
the selected Database in a table named auth_keys. 

Supported Database drivers are:
  - postrgesql
  - mysql
  - mysql compatable e.g. mariadb, aurora
  - sqlite

You may need to install the specific database driver for your selected database, more information can be 
found at https://pypi.org/project/databases/

.. code-block: bash

  $ pip install databases[postgresql]
  $ pip install databases[mysql]
  $ pip install databases[sqlite]


Using SQLite with this auth mechanism requires JSON support that can be found in SQLite version > 3.3 and Python3
Previous versions of SQLite may be supported with the JSON1 SQLite extension. 


Any authentication can be included within the connection string
For example:

.. code-block:: bash

    hpfeeds-broker -e tcp:port=20000 --exporter=0.0.0.0:9431 --auth="database+mysql://username:password@127.0.0.1/example"


.. code-block:: bash

    hpfeeds-broker -e tcp:port=20000 --exporter=0.0.0.0:9431 --auth="database+postgresql://localhost/example"

.. code-block:: bash

    hpfeeds-broker -e tcp:port=20000 --exporter=0.0.0.0:9431 --auth="database+sqlite:///auth_keys.db"

To create the tables under mysql or sqlite

.. code-block:: sql

    CREATE TABLE `auth_keys` (
      `id` int AUTO_INCREMENT NOT NULL ,
      `identifier` varchar(36) DEFAULT NULL,
      `secret` varchar(36) DEFAULT NULL,
      `publish` json DEFAULT NULL,
      `subscribe` json DEFAULT NULL,
      PRIMARY KEY (`id`)
    )

To create the tables for a PostgreSQL Database

.. code-block:: sql

    CREATE SEQUENCE auth_keys_seq;

    CREATE TABLE auth_keys (
      id int NOT NULL DEFAULT NEXTVAL ('auth_keys_seq'),
      identifier varchar(36) DEFAULT NULL,
      secret varchar(36) DEFAULT NULL,
      publish json DEFAULT NULL,
      subscribe json DEFAULT NULL,
      PRIMARY KEY (id)
    )

To add a new user

.. code-block:: bash

    mysql -u admin -p <password>
    use database_name;
    
    mysql> INSERT INTO auth_keys (identifier, secret, publish, subscribe) VALUES ('testing', 'secretkey', '["channel1", "channel2"]', '["channel2"]');
    Query OK, 1 row affected (0.00 sec)


To Find all users

.. code-block:: bash

    mysql -u admin -p <password>
    use database_name;

    mysql> select * from auth_keys;
    +----+------------+-----------+--------------------------+--------------+
    | id | identifier | secret    | publish                  | subscribe    |
    +----+------------+-----------+--------------------------+--------------+
    |  1 | testing    | secretkey | ["channel1", "channel2"] | ["channel2"] |
    +----+------------+-----------+--------------------------+--------------+
    1 row in set (0.00 sec)



SQLite authentication store
---------------------------

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
        
When you start this example with `docker-compose up` it will automatically create an empty sqlite database in `/app/var` for you.

Unfortunately managing access keys currently involves SQL! You can use
docker-compose to get an sqlite shell with:

.. code-block:: bash

   $ docker-compose run --rm hpfeeds sqlite3 sqlite.db

You can list users with

.. code-block:: sql

    SELECT * FROM authkeys;

You can insert users with:

.. code-block:: sql

    INSERT INTO authkeys (owner, ident, secret, pubchans, subchans)
        VALUES ('owner', 'ident', 'secret', '["chan1"]', '["chan1"]');
        
pubchans and subchans are JSON encoded lists.

You don't need to restart the broker.


Mongo authentication store
--------------------------

When starting the broker you can pass a mongo connection string. Auth requests are then checked against
the selected Database in a collection named auth_keys. Any authentication can be included within the connection string
For example:

.. code-block:: bash

    hpfeeds-broker -e tcp:port=20000 --exporter=0.0.0.0:9431 --auth="mongodb://127.0.0.1:27017/hpfeeds"

.. code-block:: bash

    hpfeeds-broker -e tcp:port=20000 --exporter=0.0.0.0:9431 --auth="mongodb://admin:admin@127.0.0.1:27017/hpfeeds"

An example Mongo Document:

.. code-block:: json

    {
      "identifier": "testing",
      "secret": "secretkey",
      "publish": [ "chan1","chan2"],
      "subscribe": ["chan2"]
    }

To Find all users

.. code-block:: bash

    mongo
    > use hpfeeds
    switched to db hpfeeds
    > show collections
    auth_key
    > db.auth_key.find()
    { "_id" : ObjectId("5e35e5f09ba2a06adeef5be0"), "identifier" : "49be3430-4535-11ea-90b0-0242ac140004", "secret" :     "q8JeUC043OYs7Mmz", "publish" : [ ], "subscribe" : [ ] }
    > 

To add a new user

.. code-block:: bash

    mongo -u admin -padmid
    > use hpfeeds
    switched to db hpfeeds
    > db.auth_key.insert({"identifier": "testing", "secret": "secretkey", "publish": ["chan1", "chan2"], subscribe: ["chan2"]})
    WriteResult({ "nInserted" : 1 })
    > 


TLS
===

You can use a self-signed certificate:

.. code-block:: bash

    $ openssl req -x509 -newkey rsa:2048 -keyout broker.key -nodes \
        -out broker.crt -sha256 -days 1000

You can start the broker using this cert with::

    $  hpfeeds-broker --endpoint=tls:port=10000:key=broker.key:cert=broker.crt

Or if using docker-compose:

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
          
If you use letsencrypt to issue this certificate and have `aionotify` installed on a Linux machine then the certificate will be automatically rolled over without having to restart the broker.


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

The same config with docker-compose:

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

The intention is that you could have a pull only side and a push only side, but this is not yet implemented.


Without Docker
==============

You can also install the python package directly:

.. code-block:: bash

   $ pip install hpfeeds[broker]

You can then run it in the foreground with:

.. code-block:: bash

    $ hpfeeds-broker -e tcp:port=10000 --name mybroker

This will run in the foreground - use systemd to run this as a production server.
