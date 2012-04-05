import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import settings

from django.core.mail import send_mail

send_mail('Subject here', 'Here is the message.', 'admin@hpfeeds.honeycloud.net',
    ['mark@etcho.de'], fail_silently=False)
