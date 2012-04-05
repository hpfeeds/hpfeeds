import collections
from mongoengine import *

from hpfeedauth import User

class TagRights(Document):
    tag = StringField(max_length=50, required=True)
    subscribe = ListField(StringField(), default=[])
    publish = ListField(StringField(), default=[])

    def __unicode__(self):
        return self.tag

class AuthKey(Document):
	owner = ReferenceField(User)
	identifier = StringField(max_length=20, required=True)
	secret = StringField(max_length=40, required=True)
	subscribe = ListField(StringField(), default=[])
	publish = ListField(StringField(), default=[])
	comment = StringField(max_length=100, required=False)
	template = BooleanField(default=False)

	def __unicode__(self):
		return '<AK: {0}{1}>'.format(self.identifier, ' ('+self.comment+')' if self.comment else '')

class Chanstat(Document):
	name = StringField(required=True, unique=True)
	total = IntField(required=True, default=0)
	sourcecount = IntField(required=True, default=0)
	hour = IntField(required=True, default=0)
	day = IntField(required=True, default=0)
	week = IntField(required=True, default=0)

class Publog(Document):
	tstamp = DateTimeField(required=True)
	chan = StringField(required=True)
	identifier = StringField(max_length=20, required=True)

class Channel(Document):
	tstamp = DateTimeField()
	creator = ReferenceField(User)
	name = StringField()
	description = StringField()
	subscribe = ListField(StringField(), default=[])
	publish = ListField(StringField(), default=[])
	pubtags = ListField(StringField(), default=[])
	subtags = ListField(StringField(), default=[])

	def __unicode__(self):
		return '<Channel: {0}>'.format(self.name)

	def access_user(self, user):
		out = set()
		un = user.username
		if un in self.publish: out.add('pub')
		if un in self.subscribe: out.add('sub')
		for tag in user.tags + ['anyone',]:
			if tag in self.pubtags: out.add('pub')
			if tag in self.subtags: out.add('sub')
		return ','.join(out)

	def access_dict(self):
		useraxs = collections.defaultdict(set)
		for un in self.publish: useraxs[un].add('pub')
		for un in self.subscribe: useraxs[un].add('sub')
		for k in useraxs: useraxs[k] = ','.join(useraxs[k])
		return useraxs

	def delete(self, *args, **kwargs):
		# delete my name from all authkeys
		aks = AuthKey.objects(Q(publish=self.name)|Q(subscribe=self.name))
		for ak in aks:
			if self.name in ak.publish: ak.publish.remove(self.name)
			if self.name in ak.subscribe: ak.subscribe.remove(self.name)
			ak.save()

		super(Document, self).delete(*args, **kwargs)
		# deleted

	def anypub(self):
		return 'anyone' in self.pubtags
	def anysub(self):
		return 'anyone' in self.subtags


