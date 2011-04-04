# Django settings for hpfeedweb project.

import os
PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))

import mongoengine
mongoengine.connect('hpfeeds')

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
	('Mark Schloesser', 'ms@mwcollect.org'),
)

MANAGERS = ADMINS

TIME_ZONE = 'Europe/Berlin'
LANGUAGE_CODE = 'en-us'

SITE_ID = 1
USE_I18N = False
USE_L10N = False

MEDIA_ROOT = os.path.join(PROJECT_PATH, 'static')
MEDIA_URL = '/static/'

SECRET_KEY = 'tv5vn5gwcmni1q-jgmf1skh)$d4m^0b9-farb16^zpcdi74i!p'

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'exchandler.SimpleExceptionResponse',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
#    'django.contrib.messages.middleware.MessageMiddleware',
)

AUTHENTICATION_BACKENDS = (
    'hpfeedauth.MongoEngineBackend',
)

SESSION_ENGINE = 'mongoengine.django.sessions'

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
	os.path.join(PROJECT_PATH, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.sessions',
)

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

