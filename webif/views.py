import collections
import random
import string
import json
import datetime

from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

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

@login_required
def overview(request):
	channelaxs = getchanaxs(request.user)
	strchanaxs = [(chan, ','.join(axs)) for chan, axs in channelaxs.items()]
	authkeys = AuthKey.objects.filter(owner=request.user)

	return render_to_response('overview.html', {'authkeys': authkeys, 'channels': strchanaxs}, context_instance=RequestContext(request))

@login_required
def ajoverview(request):
	return render_to_response('ajoverview.html', {}, context_instance=RequestContext(request))

@login_required
def ajchannels(request):
	channelaxs = getchanaxs(request.user)
	strchanaxs = [(chan, ','.join(axs)) for chan, axs in channelaxs.items()]
	return HttpResponse(json.dumps(strchanaxs), mimetype='application/json')

@login_required
def ajauthkeys(request):
	authkeys = [i.identifier for i in AuthKey.objects.filter(owner=request.user)]
	return HttpResponse(json.dumps(authkeys), mimetype='application/json')

@login_required
def newchan(request):
	if request.method == 'POST' and 'cname' in request.POST:
		cname = request.POST['cname']
		for c in cname:
			if c not in string.lowercase + '.-' + string.digits:
				return render_to_response('fail.html')

		if not TagRights.objects.filter(publish=cname) and \
		  not TagRights.objects.filter(subscribe=cname) and \
		  not User.objects.filter(publish=cname) and \
		  not User.objects.filter(subscribe=cname):
			request.user.publish.append(request.POST['cname'])
			request.user.subscribe.append(request.POST['cname'])
			request.user.save()
		else:
			return render_to_response('fail.html', {'msg': 'That channel exists.'})

	return redirect(overview)

@login_required
def editchan(request, ch):
	uaxs = getchanaxs(request.user)
	if not ch in uaxs:
		return redirect(overview)

	if request.method == 'POST' and 'cname' in request.POST and 'axs' in request.POST:
		uname = request.POST['cname']
		try:
			uobj = User.objects.get(username=uname)
		except:
			return render_to_response('fail.html', {'msg': 'Can not find username.'})
		
		naxs = request.POST['axs']
		uaxs = getchanaxs(request.user)
		if ch in uaxs:
			if naxs == 'pub' or naxs == 'both' and 'pub' in uaxs[ch]:
				uobj.publish.append(ch)
			if naxs == 'sub' or naxs == 'both' and 'sub' in uaxs[ch]:
				uobj.subscribe.append(ch)
			uobj.save()

	if request.method == 'POST' and 'delete' in request.POST:
		if len(useraxs) < 2 and len(tagaxs) == 0:
			request.user.publish.remove(ch)
			request.user.subscribe.remove(ch)
			request.user.save()
		return redirect(overview)

	useraxs, tagaxs = getaxs4chan(ch)

	struseraxs = [(user, ','.join(axs)) for user, axs in useraxs.items()]
	strtagaxs = [(tag, ','.join(axs)) for tag, axs in tagaxs.items()]
	
	return render_to_response('editchan.html', {'chan': ch, 'users': struseraxs, 'tags': strtagaxs}, context_instance=RequestContext(request))

def randstr(length):
	return ''.join([random.choice(string.lowercase+string.digits) for i in range(length)])

@login_required
def newak(request):
	identifier = randstr(5) + '@hp1'
	while AuthKey.objects.filter(identifier=identifier):
		identifier = randstr(5) + '@hp1'
	secret = randstr(16)

	nak = AuthKey(identifier=identifier, secret=secret, publish=[], subscribe=[], owner=request.user)
	nak.save()
	
	return render_to_response('newak.html', {'ak': nak}, context_instance=RequestContext(request))

@login_required
def editak(request, ak):
	try:
		akobj = AuthKey.objects.get(identifier=ak)
	except:
		return render_to_response('fail.html')

	if request.method == 'POST' and 'cname' in request.POST and 'axs' in request.POST:
		cname = request.POST['cname']
		naxs = request.POST['axs']
		uaxs = getchanaxs(request.user)
		if cname in uaxs:
			if naxs == 'pub' or naxs == 'both':
				akobj.publish.append(cname)
			if naxs == 'sub' or naxs == 'both':
				akobj.subscribe.append(cname)
			akobj.save()

	if request.method == 'POST' and 'delete' in request.POST:
		akobj.delete()
		return redirect(overview)

	axs = collections.defaultdict(set)
	for c in akobj.publish:
		axs[c].add('pub')
	for c in akobj.subscribe:
		axs[c].add('sub')
	straxs = [(chan, ','.join(v)) for chan, v in axs.items()]
	
	return render_to_response('editak.html', {'ak': akobj, 'axs': straxs}, context_instance=RequestContext(request))

