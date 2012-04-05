import collections
import random
import string
import json
import datetime

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.contrib.auth.views import password_change
from django.core.mail import send_mail, mail_managers
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.core import validators
from django import forms
#from django.db.models import Q
from mongoengine import Q

import settings
from hpfeedauth import User
from models import AuthKey, TagRights, Chanstat, Channel

def rtr(tpl, ctx, request):
	return render_to_response(tpl, ctx, context_instance=RequestContext(request))
def fail(msg, request):
	return render_to_response('fail.html', {'msg': msg}, context_instance=RequestContext(request))

def getchanaxs(user):
	u=user.username
	return dict([(c.name, c.access_user(user)) for c in Channel.objects(Q(publish=u) | Q(subscribe=u) | Q(subtags='anyone') | Q(pubtags='anyone'))])

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
    chapter = forms.CharField(label="HP Chapter")
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
        user = User(username=self.cleaned_data['username'], email=self.cleaned_data['email'], chapter=self.cleaned_data['chapter'], is_active=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

NEWUSER_MESSAGE = '''A new user registered on hpfeeds.honeycloud.net:
Username: {1}
E-Mail: {0}
Chapter: {2}

Please activate the user if legit: http://hpfeeds.honeycloud.net/users/

Thanks,
 hpfeeds webinterface
'''

ACTIVATED_MESSAGE = '''Your account on hpfeeds.honeycloud.net was activated!
Username: {1}
E-Mail: {0}
Chapter: {2}

You may now login and use hpfeeds at: http://hpfeeds.honeycloud.net/

Have fun!
 hpfeeds webinterface
'''

def register(request):
	if request.method == 'POST':
		uc = UserCreationForm(request.POST)
		if uc.is_valid():
			uc.save()
			mail_managers('hpfeeds.honeycloud.net registration', NEWUSER_MESSAGE.format(uc.cleaned_data['email'],uc.cleaned_data['username'], uc.cleaned_data['chapter']))
			return render_to_response('registered.html', {}, context_instance=RequestContext(request))
		else:
			return render_to_response('register.html', {'form': uc}, context_instance=RequestContext(request))
		
	uc = UserCreationForm()
	return render_to_response('register.html', {'form': uc}, context_instance=RequestContext(request))

@login_required
def channels(request):
	u = request.user.username
	axschans = Channel.objects(Q(publish=u) | Q(subscribe=u) | Q(subtags='anyone') | Q(pubtags='anyone')).order_by('name')
	restchans = Channel.objects(id__not__in=[i.id for i in axschans]).order_by('name')

	return render_to_response('channels.html', {'channels': axschans, 'restchans': restchans}, context_instance=RequestContext(request))

@login_required
def authkeys(request):
	authkeys = AuthKey.objects.filter(owner=request.user).order_by('identifier')

	return render_to_response('authkeys.html', {'authkeys': authkeys}, context_instance=RequestContext(request))

@login_required
def authkeys_all(request):
	authkeys = AuthKey.objects.filter(owner__ne=request.user).order_by('owner', 'identifier')

	return render_to_response('authkeys_all.html', {'authkeys': authkeys}, context_instance=RequestContext(request))

class NewChanForm(forms.Form):
	cname = forms.RegexField(label="Channel name", max_length=30, regex=r'^[\w.]+$',
		help_text = "May contain letters, digits, dot, dash, underscore.",
		error_messages = {'invalid': "This value may contain only letters, numbers and '.'."})
	desc = forms.CharField(label="Description", widget=forms.Textarea)

	def __init__(self, *args, **kwargs):
		forms.Form.__init__(self, *args, **kwargs)

	def clean_cname(self):
		cname = self.cleaned_data["cname"]
		a = Channel.objects.filter(name=cname).count()
		if a == 0: return cname
		#a = TagRights.objects.filter(publish=cname).count()
		#b = TagRights.objects.filter(subscribe=cname).count()
		#c = User.objects.filter(publish=cname).count()
		#d = User.objects.filter(subscribe=cname).count()
		#if a + b + c + d == 0:
		#	return cname
		raise forms.ValidationError("This channel is already in use.")

@login_required
def newchan(request):
	if request.method == 'POST':
		uc = NewChanForm(request.POST)
		if uc.is_valid():
			cname = uc.cleaned_data['cname']
			chan = Channel(name=cname, description=uc.cleaned_data['desc'], publish=[request.user.username,], subscribe=[request.user.username,], creator=request.user)
			#request.user.publish.append(cname)
			#request.user.subscribe.append(cname)
			chan.save()
			#request.user.save()
			return render_to_response('chancreated.html', {'cname': cname}, context_instance=RequestContext(request))
		else:
			return render_to_response('chancreate.html', {'form': uc}, context_instance=RequestContext(request))
		
	uc = NewChanForm()
	return render_to_response('chancreate.html', {'form': uc}, context_instance=RequestContext(request))

class UserAccessForm(forms.Form):
	uname = forms.ChoiceField(label="User", choices=[])
	axs = forms.ChoiceField(label="Access", choices=[('p', 'publish'), ('s', 'subscribe'), ('ps', 'pub/sub')])

	def __init__(self, user, *args, **kwargs):
		forms.Form.__init__(self, *args, **kwargs)
		self.user = user
		self.fields['uname'].choices = [(u.username, '{0} ({1})'.format(u.username, u.chapter)) for u in User.objects.filter(is_active=True).order_by('username') if not u.username == user.username]

	def clean_uname(self):
		username = self.cleaned_data["uname"]
		try:
			User.objects.get(username=username)
		except User.DoesNotExist:
			raise forms.ValidationError("A user with that username does not exist.")
		return username

@login_required
def editchan(request, ch):
	try: cobj = Channel.objects.get(name=ch)
	except: return fail('Could not find channel.', request)
	axs = cobj.access_user(request.user)

	if not axs: return fail('You are not allowed to edit this channel.', request)
		
	uc = UserAccessForm(request.user)

	struseraxs = cobj.access_dict().items()

	aks = collections.defaultdict(set)
	for a in AuthKey.objects.filter(owner=request.user).filter(subscribe=ch):
		aks[a.identifier].add('sub')
	for a in AuthKey.objects.filter(owner=request.user).filter(publish=ch):
		aks[a.identifier].add('pub')
	straks = [(ident, ','.join(v)) for ident, v in aks.items()]

	if request.method == 'POST':
		aks = request.POST.get('ak', None)
		ucs = request.POST.get('u', None)
		desc = request.POST.get('description', None)
		if ucs:
			uc = UserAccessForm(request.user, request.POST)
			if uc.is_valid():
				uname = uc.cleaned_data['uname']
				try: uobj = User.objects.get(username=uname)
				except: return fail('You are not allowed to edit this channel.', request)
				naxs = request.POST['axs']
				if (naxs == 'p' or naxs == 'ps') and 'pub' in axs and not uobj.username in cobj.publish:
					cobj.publish.append(uobj.username)
				if (naxs == 's' or naxs == 'ps') and 'sub' in axs and not uobj.username in cobj.subscribe:
					cobj.subscribe.append(uobj.username)
				cobj.save()
				return rtr('chanedited.html', {'ch': ch, }, request)

		if desc:
			anysub = request.POST.get('anysub', 'no')
			anypub = request.POST.get('anypub', 'no')
			cobj.description = desc
			if anysub == 'yes' and not 'anyone' in cobj.subtags:
				cobj.subtags.append('anyone')
			if anypub == 'yes' and not 'anyone' in cobj.pubtags:
				cobj.pubtags.append('anyone')
			cobj.save()

	return rtr('chanedit.html', {'aks': straks, 'form': uc, 'ch': cobj, 'users': struseraxs}, request)

@login_required
def deletechan(request, ch):
	try: cobj = Channel.objects.get(name=ch)
	except: return render_to_response('fail.html', {'msg': 'Could not find channel.'}, context_instance=RequestContext(request))

	if not cobj.creator == request.user:	
		return render_to_response('fail.html', {'msg': 'Only a channel creator may delete it.'}, context_instance=RequestContext(request))

	confirmed = request.GET.get('confirm', 'no') == 'yes'
	if confirmed:
		cobj.delete()
	
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

class AuthKeyField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return "{0} (by {1})".format(obj.comment, obj.owner.username)

class GenAKForm(forms.Form):
	comment = forms.RegexField(label="Comment", max_length=60, regex=r'^[\w@.,\-_!?() ]*$',
		error_messages = {'invalid': "Invalid character in comment."})
	tpl = AuthKeyField(label='Template', queryset=AuthKey.objects.filter(template=True), empty_label="No template", required=False)

	#def __init__(self, user=None, *args, **kwargs):
	#	self.fields['chan'].choices = [(c, c) for c in uaxs]
	#	forms.Form.__init__(self, *args, **kwargs)

@login_required
def newak(request):
	if request.method == 'POST':
		uc = GenAKForm(request.POST)
		if uc.is_valid():
			comment = uc.cleaned_data['comment']
			tplak = uc.cleaned_data['tpl']
			identifier = randstr(5) + '@hp1'
			while AuthKey.objects.filter(identifier=identifier):
				identifier = randstr(5) + '@hp1'
			secret = randstr(16)
			
			def tplfail():
				return render_to_response('fail.html', {'msg': 'Insufficient Access for using the template. Please talk to the owner and get the necessary authorization.'}, context_instance=RequestContext(request))

			if tplak:
				uaxs = getchanaxs(request.user)
				for c in tplak.publish:
					if not 'pub' in uaxs.get(c, ''): return tplfail()
				for c in tplak.subscribe:
					if not 'sub' in uaxs.get(c, ''): return tplfail()
				nak = AuthKey(identifier=identifier, secret=secret, comment=comment, publish=tplak.publish, subscribe=tplak.subscribe, owner=request.user)
			else:
				nak = AuthKey(identifier=identifier, secret=secret, comment=comment, publish=[], subscribe=[], owner=request.user)
			nak.save()
			return render_to_response('newakcreated.html', {'ak': nak,}, context_instance=RequestContext(request))
		else:
			return render_to_response('newak.html', {'form': uc, }, context_instance=RequestContext(request))
		
	uc = GenAKForm()
	return render_to_response('newak.html', {'form': uc, }, context_instance=RequestContext(request))


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
		uaxs = getchanaxs(request.user)
		pubs = set()
		subs = set()

		for row,values in request.POST.items():
			if not '|' in row: continue
			try: chan, naxs = row.split('|', 1)
			except: return render_to_response('fail.html', {'msg': 'Invalid data.'}, context_instance=RequestContext(request))
			if naxs == 'pub' and 'pub' in uaxs.get(chan, ''):
				pubs.add(chan)
			elif naxs == 'sub' and 'sub' in uaxs.get(chan, ''):
				subs.add(chan)

		submitbtn = request.POST.get('u', None)
		if submitbtn == 'Update':
			akobj.publish = list(pubs)
			akobj.subscribe = list(subs)
		elif submitbtn == 'Add':
			akobj.publish = list(pubs | set(akobj.publish))
			akobj.subscribe = list(subs | set(akobj.subscribe))
		akobj.save()
			
		return render_to_response('editak.html', {'updated': True, 'ak': akobj,}, context_instance=RequestContext(request))

	uaxs = getchanaxs(request.user)
	achans = set(akobj.publish) | set(akobj.subscribe)
	ochans = [c for c in uaxs.keys() if not c in achans]
	
	return render_to_response('editak.html', {'uaxs': uaxs, 'ak': akobj, 'achans': achans, 'ochans': ochans}, context_instance=RequestContext(request))

def index(request):
	cs = Chanstat.objects.all()
	stats = dict([(i.name, i) for i in cs])
	for i in cs: stats.update({i.name.replace('-', '_').replace('.', '_'): i})

	return render_to_response('index.html', {'cs': cs, 'stats': stats}, context_instance=RequestContext(request))

@login_required
def users(request):
	active = User.objects.filter(is_active=True).order_by('username')
	inactive = User.objects.filter(is_active__in=[False, None])

	return render_to_response('users.html', {'active': active, 'inactive': inactive}, context_instance=RequestContext(request))

class ActivateForm(forms.Form):
	comment = forms.CharField(max_length=100)

def activate_user(request, username):
	try: uobj = User.objects.get(username=username)
	except: return render_to_response('fail.html', {'msg': 'User not found.'}, context_instance=RequestContext(request))

	if request.method == 'POST':
		af = ActivateForm(request.POST)
		if af.is_valid():
			uobj.is_active = True
			uobj.comment = af.cleaned_data['comment']
			uobj.activated_by = request.user.username
			uobj.save()
			send_mail('{0}hpfeeds.honeycloud.net account activated'.format(settings.EMAIL_SUBJECT_PREFIX), ACTIVATED_MESSAGE.format(uobj.email,uobj.username, uobj.chapter), settings.SERVER_EMAIL, [uobj.email,])
			return redirect(users)
	else:
		af = ActivateForm()

	if uobj.is_active: return render_to_response('fail.html', {'msg': 'User is already active.'}, context_instance=RequestContext(request))

	return render_to_response('activate.html', {'form': af, 'uobj': uobj}, context_instance=RequestContext(request))


@login_required
def user_settings(request):
	return render_to_response('settings.html', {}, context_instance=RequestContext(request))

@csrf_exempt
def remote_ip(request):
	ip = request.META['REMOTE_ADDR']
	return HttpResponse(ip)

