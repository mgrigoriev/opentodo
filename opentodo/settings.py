# -*- coding: utf-8 -*-

# ! It is a good idea not to edit this and edit local_settings.py instead
# ! (copy local_settings.py.default to local_settings.py first)
# ! Especially if you want to update from version control system in future, because
# ! local_settings.py is not under version control

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',        # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
        'NAME': 'opentodo.db',       # Or path to database file if using sqlite3.
        'USER': '',               # Not used with sqlite3.
        'PASSWORD': '',           # Not used with sqlite3.
        'HOST': '',               # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',               # Set to empty string for default. Not used with sqlite3.
    }
}

# Absolute path to the directory that holds media.
# MEDIA_ROOT = '/var/www/opentodo_media'
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT.
# Note that this should have a trailing slash if it has a path component
# MEDIA_URL = 'http://static.myhost.ru' or MEDIA_URL = 'http://myhost.ru/static/'
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

SEND_EMAILS = False       # make it True and edit settings bellow if you want to receive emails
EMAIL_HOST = ''           # smtp.myhost.com
EMAIL_HOST_USER = ''      # user123
EMAIL_HOST_PASSWORD = ''  # qwerty
EMAIL_ADDRESS_FROM = ''   # noreply@myhost.com
if DEBUG:
    EMAIL_FAIL_SILENTLY = False
else:
    EMAIL_FAIL_SILENTLY = True

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'ih^s_r3qgx!8-7aj%7^tqg#mj&zpdmchbbc=+*9=y#cm&v(ga)'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL= '/'

import sys, os
PROJECT_DIR = os.path.dirname(__file__)
sys.path.append(PROJECT_DIR)
sys.path.append(PROJECT_DIR + '/apps')

TEMPLATE_DIRS = (
    PROJECT_DIR + '/templates'
)

TIME_ZONE = 'Europe/Moscow'
LANGUAGE_CODE = 'ru'

SITE_ID = 1
USE_I18N = True

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'todo.middleware.Custom403Middleware',
)
FILE_CHARSET = 'utf-8'

SESSION_SAVE_EVERY_REQUEST = False

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.request',
    'context_processors.host',
    'context_processors.my_media_url',
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

ROOT_URLCONF = 'urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'todo',
)

##################################################################################
# You can create local_settings.py to override the settings.
# It is recomended to put all your custom settings (database, path, etc.) there
# if you want to update from Subversion in future.
##################################################################################
try:
    from local_settings import *
except ImportError:
    pass
