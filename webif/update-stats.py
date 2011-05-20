import os
import datetime

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import settings
from models import Chanstat, Publog


cs = Chanstat.objects.all()
for i in cs:
	i.hour = Publog.objects.filter(chan=i.name, tstamp__gte=datetime.datetime.now()-datetime.timedelta(0,3600)).count()
	i.day = Publog.objects.filter(chan=i.name, tstamp__gte=datetime.datetime.now()-datetime.timedelta(1)).count()
	i.week = Publog.objects.filter(chan=i.name, tstamp__gte=datetime.datetime.now()-datetime.timedelta(7)).count()
	i.save()

