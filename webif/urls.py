from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib.auth.views import login, logout

from views import *

urlpatterns = patterns('',
    url('^$', index, name='overview'),
#    url('^overview$', overview, name='overview'),
    url('^aj$', ajoverview, name='ajoverview'),
    url('^aj/channels$', ajchannels, name='ajchannels'),
    url('^aj/authkeys$', ajauthkeys, name='ajauthkeys'),
    url('^newchan/$', newchan, name='newchan'),
    url('^editchan/([\w@-]+)/$', editchan, name='editchan'),
    url('^newak/$', newak, name='newak'),
    url('^editak/([\w@]+)/$', editak, name='editak'),
    url('^login/$', login, {'template_name': 'login.html',}, name='log-in'),
    url('^logout/$', logout, {'next_page': '/'}, name='log-out'),
)

if True or settings.DEBUG:
    urlpatterns += patterns('', 
                            (r'^' + settings.MEDIA_URL.lstrip('/') + r'(.*)$', 
                            'django.views.static.serve',
                            {'document_root': settings.MEDIA_ROOT}))
