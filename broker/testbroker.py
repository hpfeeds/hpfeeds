import sys
import feedbroker
from feedbroker import *


FeedConnOrig = FeedConn
FeedBrokerOrig = FeedBroker


class FeedBroker(FeedBrokerOrig):
	def initdb(self):
		pass


class FeedConn(FeedConnOrig):
	def auth(self, ident, hash):
		self.checkauth([{'identifier': str(ident), 'secret': 'secretsecret'},], hash)

	def checkauth(self, r, hash):
		if len(r) > 0:
			akobj = r[0]
			akhash = hashlib.sha1('{0}{1}'.format(self.rand, akobj['secret'])).digest()
			self.idents.add(akobj['identifier'])
			logging.info('Auth success by {0}.'.format(akobj['identifier']))
		else:
			self.error('authfail.')

		self.io_in(b'')

	def may_publish(self, chan):
		return True

	def may_subscribe(self, chan):
		return True


feedbroker.FeedConn = FeedConn
feedbroker.FeedBroker = FeedBroker


def main():
	fb = FeedBroker()

	loop()
	return 0

if __name__ == '__main__':
	sys.exit(main())

