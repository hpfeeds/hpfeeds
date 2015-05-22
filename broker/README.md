# hpfeeds broker

## Adding a user (new sensor or new client)

The hpfeeds broker stores user credentials in mongodb.  The `add_user.py` and `dump_users.py` scripts assist in setting up new users and troubleshooting.  `add_user.py` can also be used to update an existing user.  

Adding a new sensor (publish only)

    $ python add_user.py dionaea.1234 6t5r4e46g7y8j8 dionaea.events,dionaea.capture ""
    inserted {'subscribe': [], 'secret': '6t5r4e46g7y8j8', 'identifier': 'dionaea.1234', 'publish': ['dionaea.events', 'dionaea.capture']}

Adding a new client (subscribe only)

    $ python add_user.py webapp.4567 p0o9i8u7ycj "" dionaea.events,dionaea.capture
    inserted {'subscribe': ['dionaea.events', 'dionaea.capture'], 'secret': 'p0o9i8u7ycj', 'identifier': 'webapp.4567', 'publish': []}

Updating a user:

	$ python add_user.py webapp.4567 abc12345678 "" dionaea.events,dionaea.capture,thug.files,kippo.events
	updated {'subscribe': ['dionaea.events', 'dionaea.capture', 'thug.files', 'kippo.events'], 'secret': 'abc12345678', 'identifier': 'webapp.4567', 'publish': []}

## Dumping the users from mongodb

    $ python dump_users.py
	{u'subscribe': [], u'secret': u'6t5r4e46g7y8j8', u'_id': ObjectId('5368e587b391d1d314123a33'), u'publish': [u'dionaea.events', u'dionaea.capture'], u'identifier': u'dionaea.1234'}
	{u'subscribe': [u'dionaea.events', u'dionaea.capture'], u'secret': u'p0o9i8u7ycj', u'_id': ObjectId('5368e5d7b391d1d314123a34'), u'publish': [], u'identifier': u'webapp.4567'}

## Running the Broker

	$ python feedbroker.py

