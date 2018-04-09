hpfeeds3
========

[![PyPI](https://img.shields.io/pypi/v/hpfeeds3.svg)](https://pypi.python.org/pypi/hpfeeds3) [![Codecov](https://img.shields.io/codecov/c/github/Jc2k/hpfeeds3.svg)](https://codecov.io/gh/Jc2k/hpfeeds3)

This is a python 3 compatible implementation of hpfeeds. Check out the following implementations:

 - Python 2: https://github.com/rep/hpfeeds
 - Go: https://github.com/fw42/go-hpfeeds
 - Ruby: https://github.com/fw42/hpfeedsrb
 - More Ruby: https://github.com/vicvega/hpfeeds-ruby
 - JS (within node.js): https://github.com/fw42/honeymap/blob/master/server/node_modules/hpfeeds/index.js
 - C++: https://github.com/tentacool/tentacool

## About

hpfeeds is a lightweight authenticated publish-subscribe protocol that supports arbitrary binary payloads.

We tried to design a simple wire-format so that everyone is able to subscribe to the feeds with his favorite language in almost no time.

Different feeds are separated by channels and support arbitrary binary payloads. This means that the channel users have to decide about the structure of data. This could for example be done by choosing a serialization format.

Access to channels is given to so-called Authkeys which essentially are pairs of an identifier and a secret. The secret is sent to the server by hashing it together with a per-connection nonce. This way no eavesdroppers can obtain valid credentials. Optionally the protocol can be run on top of SSL/TLS, of course.

To support multiple data sources and sinks per user we manage the Authkeys in this webinterface after a quick login with a user account. User accounts are only needed for the webinterface - to use the data feed channels, only Authkeys are necessary. Different Authkeys can be granted distinct access rights for channels.

## Installation

```
git clone https://github.com/rep/hpfeeds/
cd hpfeeds
python setup.py build
python setup.py install
```

## Wire Protocol

Each message carries a message header. The message types can make use of "parameters" that are being sent as (length,data) pairs.

```
struct MsgHeader {
    uint32_t messageLength; // total message size, including this
    uint8_t opCode;        // request type - see table below
};
```

For example the publish message would consist of message header, length(client_id), client id, length(channelname), channelname, payload. The payload, can be arbitrary binary data.
On the wire this would look like:

```
length | opcode | next | identifier | next | channelname | payload
----------------------------------------------------------------------------------------------------------------------------
    85        3   9      b4aa2@hp1    9      mwcapture     137941a3d8589f6728924c08561070bceb5d72b8,http://1.2.3.4/calc.exe
```

### Message types

* error (0): errormessage
* info (1): server name, nonce
* auth (2): client id, sha1(nonce+authkey)
* publish (3): client id, channelname, payload
* subscribe (4): client id, channelname
* For further details and definition of each message type, consider the page about the example CLI which describes how to speak the wire protocol.

### Authentication

* Server sends a nonce per connection
* Client sends id and sha1(nonce+authkey) hash
* Server looks up authkey by id and checks hash
* Server looks up subscribe/publish ACL for this client
