from mongoengine import *

from hpfeedauth import User

class TagRights(Document):
    tag = StringField(max_length=50, required=True)
    subscribe = ListField(StringField())
    publish = ListField(StringField())

    def __unicode__(self):
        return self.tag

class AuthKey(Document):
	owner = ReferenceField(User)
	identifier = StringField(max_length=20, required=True)
	secret = StringField(max_length=40, required=True)
	subscribe = ListField(StringField())
	publish = ListField(StringField())
	comment = StringField(max_length=100, required=False)

	def __unicode__(self):
		return '<AK: {0}{1}>'.format(self.identifier, ' ('+self.comment+')' if self.comment else '')

