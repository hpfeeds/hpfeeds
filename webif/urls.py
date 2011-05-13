from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib.auth.views import login, logout

from views import *

urlpatterns = patterns('',
    url('^$', index, name='index'),
    url('^channels/$', channels, name='channels'),
    url('^authkeys/$', authkeys, name='authkeys'),
    url('^newchan/$', newchan, name='newchan'),
    url('^editchan/([\w@_\-.]+)/$', editchan, name='editchan'),
    url('^deletechan/([\w@_\-.]+)/$', deletechan, name='deletechan'),
    url('^newak/$', newak, name='newak'),
    url('^editak/([\w@]+)/$', editak, name='editak'),
    url('^deleteak/([\w@]+)/$', deleteak, name='deleteak'),
    url('^register/$', register, name='register'),
    url('^login/$', login, {'template_name': 'login.html',}, name='log-in'),
    url('^logout/$', logout, {'next_page': '/'}, name='log-out'),
)

if True or settings.DEBUG:
    urlpatterns += patterns('', 
                            (r'^' + settings.MEDIA_URL.lstrip('/') + r'(.*)$', 
                            'django.views.static.serve',
                            {'document_root': settings.MEDIA_ROOT}))
