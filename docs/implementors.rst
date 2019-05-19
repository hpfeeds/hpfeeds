Implementors Reference
======================

You can quickly get started with hpfeeds - establish a connection and start
firing data at a channel - but here are some things to think about first based
on our experience with hpfeeds.


Choosing the right implementation
---------------------------------

Using the blocking client with a Twisted project works but is not ideal. We
ship a Twisted implementation of hpfeeds that won't block the event loop when
writing.

Care needs to be taken with gevent - whilst using the blocking client seems
straight forward under heavy load you will get packet corruption unless you
serialize socket writes. Either wrap writes with a ``gevent.coros.RLock`` or add
a write queue.


Data format
-----------

For better or worse hpfeeds doesn't require you to use any particular data
format.

You should chose a format that is easy for machine processing. For example,
if you plan to ingest the data with logstash you could write JSON data to
hpfeeds.

If writing binary blobs, remember that there is a maximum payload size.
