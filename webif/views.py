import collections
import random
import string
import json
import datetime

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.core import validators
from django import forms
from django.db.models import Q

from hpfeedauth import User
from models import AuthKey, TagRights

def getchanaxs(user):
	channelaxs = collections.defaultdict(set)
	for c in user.publish:
		channelaxs[c].add('pub')
	for c in user.subscribe:
		channelaxs[c].add('sub')
	for tag in user.tags:
		try:
			tr = TagRights.objects.get(tag=tag)
		except:
			continue
		for c in tr.publish:
			channelaxs[c].add('pub')
		for c in tr.subscribe:
			channelaxs[c].add('sub')
	return channelaxs

def getaxs4chan(chan):
	useraxs = collections.defaultdict(set)
	tagaxs = collections.defaultdict(set)
	for u in User.objects.filter(publish=chan):
		useraxs[u.username].add('pub')
	for u in User.objects.filter(subscribe=chan):
		useraxs[u.username].add('sub')
	for tag in TagRights.objects.filter(publish=chan):
		tagaxs[tag.tag].add('pub')
	for tag in TagRights.objects.filter(subscribe=chan):
		tagaxs[tag.tag].add('sub')
	return useraxs, tagaxs

class RegisterForm(forms.Form):
	username = forms.CharField(max_length=20)
	email = forms.CharField(max_length=100)
	passwd = forms.CharField()

class UserCreationForm(forms.Form):
    """
    A form that creates a user, with no privileges, from the given username and password.
    """
    username = forms.RegexField(label="Username", max_length=30, regex=r'^[\w]+$',
        help_text = "Required. 30 characters or fewer. Letters and digits only.",
        error_messages = {'invalid': "This value may contain only letters and numbers."})
    email = forms.CharField(label="E-Mail", help_text="Required for administrative notifications.",
        error_messages = {'invalid': "Please enter a valid E-Mail address."}, validators = [validators.validate_email,])
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput,
        help_text = "Password verification.")

    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            User.objects.get(username=username)
        except User.DoesNotExist:
            return username
        raise forms.ValidationError("A user with that username already exists.")

    def clean_email(self):
        email = self.cleaned_data['email']
        try:
            User.objects.get(email=email)
        except User.DoesNotExist:
            return email
        raise forms.ValidationError("A user with that E-Mail address already exists.")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if len(password1) < 6: raise forms.ValidationError("Password too short.")
        if password1 != password2:
            raise forms.ValidationError("The two password fields didn't match.")
        return password2

    def save(self, commit=True):
        user = User(username=self.cleaned_data['username'], email=self.cleaned_data['email'])
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

def register(request):
	if request.method == 'POST':
		uc = UserCreationForm(request.POST)
		if uc.is_valid():
			uc.save()
			return render_to_response('registered.html', {}, context_instance=RequestContext(request))
		else:
			return render_to_response('register.html', {'form': uc}, context_instance=RequestContext(request))
		
	uc = UserCreationForm()
	return render_to_response('register.html', {'form': uc}, context_instance=RequestContext(request))

@login_required
def channels(request):
	channelaxs = getchanaxs(request.user)
	strchanaxs = [(chan, ','.join(axs)) for chan, axs in channelaxs.items()]

	return render_to_response('channels.html', {'channels': strchanaxs}, context_instance=RequestContext(request))

@login_required
def authkeys(request):
	authkeys = AuthKey.objects.filter(owner=request.user)

	return render_to_response('authkeys.html', {'authkeys': authkeys}, context_instance=RequestContext(request))

class NewChanForm(forms.Form):
	cname = forms.RegexField(label="Channel name", max_length=30, regex=r'^[\w.]+$',
		help_text = "May contain letters, digits, dot, dash, underscore. Will be prepended with a prefix of your username.",
		error_messages = {'invalid': "This value may contain only letters, numbers and '.'."})

	def __init__(self, username='', *args, **kwargs):
		forms.Form.__init__(self, *args, **kwargs)
		self.username = username

	def clean_cname(self):
		cname = self.username + '.' + self.cleaned_data["cname"]
		a = TagRights.objects.filter(publish=cname).count()
		b = TagRights.objects.filter(subscribe=cname).count()
		c = User.objects.filter(publish=cname).count()
		d = User.objects.filter(subscribe=cname).count()
		if a + b + c + d == 0:
			return cname
		raise forms.ValidationError("This channel is already in use.")

@login_required
def newchan(request):
	if request.method == 'POST':
		uc = NewChanForm(request.user.username, request.POST)
		if uc.is_valid():
			cname = uc.cleaned_data['cname']
			request.user.publish.append(cname)
			request.user.subscribe.append(cname)
			request.user.save()
			return render_to_response('chancreated.html', {'cname': cname}, context_instance=RequestContext(request))
		else:
			return render_to_response('chancreate.html', {'form': uc}, context_instance=RequestContext(request))
		
	uc = NewChanForm()
	return render_to_response('chancreate.html', {'form': uc}, context_instance=RequestContext(request))

class UserAccessForm(forms.Form):
	uname = forms.RegexField(label="User", max_length=30, regex=r'^[\w]+$',
		error_messages = {'invalid': "This value may contain only letters, digits."})
	axs = forms.ChoiceField(label="Access", choices=[('p', 'publish'), ('s', 'subscribe'), ('ps', 'pub/sub')])

	def clean_uname(self):
		username = self.cleaned_data["uname"]
		try:
			User.objects.get(username=username)
		except User.DoesNotExist:
			raise forms.ValidationError("A user with that username does not exist.")
		return username

class AKAccessForm(forms.Form):
#	ident = forms.RegexField(label="Identifier", max_length=30, regex=r'^[\w@]+$',
#		error_messages = {'invalid': "This value may contain only letters, digits and @."})
	ident = forms.ChoiceField(label="Authkey", choices=[])
	axs = forms.ChoiceField(label="Access", choices=[('p', 'publish'), ('s', 'subscribe'), ('ps', 'pub/sub')])

	def __init__(self, *args, **kwargs):
		forms.Form.__init__(self, *args, **kwargs)
		self.fields['ident'].choices = [(a.identifier, unicode(a)) for a in AuthKey.objects.all()]

	def clean_ident(self):
		ident = self.cleaned_data["ident"]
		try:
			ak = AuthKey.objects.get(identifier=ident)
		except User.DoesNotExist:
			raise forms.ValidationError("An authkey with that identifier does not exist.")
		return ak


@login_required
def editchan(request, ch):
	uaxs = getchanaxs(request.user)
	if not ch in uaxs:
		return render_to_response('fail.html', {'msg': 'You are not allowed to edit this channel.'}, context_instance=RequestContext(request))
		
	uc = UserAccessForm()
	ak = AKAccessForm()

	if request.method == 'POST':
		aks = request.POST.get('ak', None)
		ucs = request.POST.get('u', None)
		if ucs:
			uc = UserAccessForm(request.POST)
			if uc.is_valid():
				uname = uc.cleaned_data['uname']
				uobj = User.objects.get(username=uname)
				naxs = request.POST['axs']
				uaxs = getchanaxs(request.user)
				if naxs == 'p' or naxs == 'ps' and 'pub' in uaxs[ch]:
					uobj.publish.append(ch)
				if naxs == 's' or naxs == 'ps' and 'sub' in uaxs[ch]:
					uobj.subscribe.append(ch)
				uobj.save()
				return render_to_response('chanedited.html', {'ch': ch, }, context_instance=RequestContext(request))
			else:
				return render_to_response('chanedit.html', {'form': uc, 'form2': ak, 'ch': ch}, context_instance=RequestContext(request))

		if aks:
			ak = AKAccessForm(request.POST)
			if ak.is_valid():
				akobj = ak.cleaned_data['ident']
				naxs = request.POST['axs']
				if naxs == 'p' or naxs == 'ps':
					akobj.publish.append(ch)
				if naxs == 's' or naxs == 'ps':
					akobj.subscribe.append(ch)
				akobj.save()
				return render_to_response('chanedited.html', {'ch': ch, }, context_instance=RequestContext(request))
			else:
				return render_to_response('chanedit.html', {'form': uc, 'form2': ak, 'ch': ch}, context_instance=RequestContext(request))

	useraxs, tagaxs = getaxs4chan(ch)

	struseraxs = [(user, ','.join(axs)) for user, axs in useraxs.items()]
	strtagaxs = [(tag, ','.join(axs)) for tag, axs in tagaxs.items()]
	aks = collections.defaultdict(set)
	for a in AuthKey.objects.filter(owner=request.user).filter(subscribe=ch):
		aks[a.identifier].add('sub')
	for a in AuthKey.objects.filter(owner=request.user).filter(publish=ch):
		aks[a.identifier].add('pub')

	straks = [(ident, ','.join(v)) for ident, v in aks.items()]

	return render_to_response('chanedit.html', {'aks': straks, 'form': uc, 'form2': ak, 'ch': ch, 'users': struseraxs}, context_instance=RequestContext(request))

@login_required
def deletechan(request, ch):
	uaxs = getchanaxs(request.user)
	if not ch in uaxs:
		return render_to_response('fail.html', {'msg': 'You are not allowed to delete this channel.'}, context_instance=RequestContext(request))

	useraxs, tagaxs = getaxs4chan(ch)
	confirmed = request.GET.get('confirm', 'no') == 'yes'
	if confirmed:
		if len(useraxs) < 2 and len(tagaxs) == 0:
			request.user.publish.remove(ch)
			request.user.subscribe.remove(ch)
			request.user.save()
			return render_to_response('deletechan.html', {'deleted': True, 'ch': ch}, context_instance=RequestContext(request))
		else:
			return render_to_response('fail.html', {'msg': 'Other users still have access to this channel.'}, context_instance=RequestContext(request))
	
	return render_to_response('deletechan.html', {'deleted': False, 'ch': ch}, context_instance=RequestContext(request))

@login_required
def deleteak(request, ident):
	try: akobj = AuthKey.objects.get(identifier=ident, owner=request.user)
	except: return render_to_response('fail.html', {'msg': 'Authkey object not found.'}, context_instance=RequestContext(request))

	confirmed = request.GET.get('confirm', 'no') == 'yes'
	if confirmed:
		akobj.delete()
		return render_to_response('deleteak.html', {'deleted': True, 'ak': akobj}, context_instance=RequestContext(request))
	
	return render_to_response('deleteak.html', {'deleted': False, 'ak': akobj}, context_instance=RequestContext(request))

def randstr(length):
	return ''.join([random.choice(string.lowercase+string.digits) for i in range(length)])

class GenAKForm(forms.Form):
	 comment = forms.RegexField(label="Comment", max_length=60, regex=r'^[\w@.,\-_!?()]+$',
		error_messages = {'invalid': "Invalid character in comment."})

@login_required
def newak(request):
	if request.method == 'POST':
		uc = GenAKForm(request.POST)
		if uc.is_valid():
			comment = uc.cleaned_data['comment']
			identifier = randstr(5) + '@hp1'
			while AuthKey.objects.filter(identifier=identifier):
				identifier = randstr(5) + '@hp1'
			secret = randstr(16)

			nak = AuthKey(identifier=identifier, secret=secret, comment=comment, publish=[], subscribe=[], owner=request.user)
			nak.save()
			return render_to_response('newakcreated.html', {'ak': nak,}, context_instance=RequestContext(request))
		else:
			return render_to_response('newak.html', {'form': uc}, context_instance=RequestContext(request))
		
	uc = GenAKForm()
	return render_to_response('newak.html', {'form': uc}, context_instance=RequestContext(request))


class ChanAccessForm(forms.Form):
	chan = forms.ChoiceField(label="Channel", choices=[])
	axs = forms.ChoiceField(label="Access", choices=[('p', 'publish'), ('s', 'subscribe'), ('ps', 'pub/sub')])

	def __init__(self, user=None, *args, **kwargs):
		forms.Form.__init__(self, *args, **kwargs)
		self.uobj = user
		uaxs = getchanaxs(user)
		self.fields['chan'].choices = [(c, c) for c in uaxs]

	def clean_chan(self):
		uaxs = getchanaxs(self.uobj)
		chan = self.cleaned_data["chan"]
		if not chan in uaxs:
			raise forms.ValidationError("Invalid channel.")
		return chan

@login_required
def editak(request, ak):
	try: akobj = AuthKey.objects.get(identifier=ak)
	except: return render_to_response('fail.html', {'msg': 'Authkey object not found.'}, context_instance=RequestContext(request))

	if request.method == 'POST':
		caf = ChanAccessForm(request.user, request.POST)
		if caf.is_valid():
			chan = caf.cleaned_data['chan']
			naxs = caf.cleaned_data['axs']
			uaxs = getchanaxs(request.user)
			if naxs == 'p' or naxs == 'ps':
				if not 'pub' in uaxs[chan]:
					return render_to_response('fail.html', {'msg': 'Insufficient access.'}, context_instance=RequestContext(request))
				akobj.publish.append(chan)
			if naxs == 's' or naxs == 'ps':
				if not 'pub' in uaxs[chan]:
					return render_to_response('fail.html', {'msg': 'Insufficient access.'}, context_instance=RequestContext(request))
				akobj.subscribe.append(chan)
			akobj.save()
			return render_to_response('editak.html', {'addedaccess': True, 'ak': akobj, 'chan': chan}, context_instance=RequestContext(request))
		else:
			return render_to_response('editak.html', {'form': caf, 'ak': akobj, 'axs': straxs}, context_instance=RequestContext(request))
			

	axs = collections.defaultdict(set)
	for c in akobj.publish:
		axs[c].add('pub')
	for c in akobj.subscribe:
		axs[c].add('sub')
	straxs = [(chan, ','.join(v)) for chan, v in axs.items()]
	
	caf = ChanAccessForm(request.user)
	return render_to_response('editak.html', {'form': caf, 'ak': akobj, 'axs': straxs}, context_instance=RequestContext(request))

def index(request):
	return render_to_response('index.html', {}, context_instance=RequestContext(request))

