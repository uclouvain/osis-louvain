##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import os

from django.utils.translation import ugettext_lazy as _
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.8/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'chgajy@#q91^!6owmz29%@#3jw094@yr@1!6w3lxx@n6v!7nvd'

ADMIN_URL = '9yk!hw9ra/'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_jenkins',
    'analytical',
    'osis_common',
    'ckeditor',
    'reference',
    'base',
    'attribution',
    'assistant',
    'dissertation',
    'internship',
    'admission',
    'localflavor',
)

# check if we are testing right now
TESTING = 'test' in sys.argv

if TESTING:
    # add test packages that have specific models for tests
    INSTALLED_APPS = INSTALLED_APPS + (
        'osis_common.tests',
    )

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'backoffice.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': []
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'base.views.common.environnement_request_processor',
            ],
        },
    },
]

WSGI_APPLICATION = 'backoffice.wsgi.application'

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'osis_backend_dev',
        'USER': os.environ.get("POSTGRES_USER") or "osis_usr",
        'PASSWORD': os.environ.get("POSTGRES_PASSWORD") or "osis",
        'HOST': os.environ.get("POSTGRES_HOST") or "127.0.0.1",
        'PORT': '5432',
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s %(levelname)s %(module)s %(process)d %(thread)d %(message)s',
            'datefmt': '%d-%m-%Y %H:%M:%S'
        },
        'simple': {
            'format': '%(asctime)s %(levelname)s %(message)s',
            'datefmt': '%d-%m-%Y %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
            'level':'DEBUG',
        },
    },
    'loggers': {
        'default': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'queue_exception': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        }
    },
}

DEFAULT_LOGGER = 'default'
QUEUE_EXCEPTION_LOGGER = 'queue_exception'

# Internationalization
# https://docs.djangoproject.com/en/1.8/topics/i18n/
LANGUAGE_CODE = 'fr-be'

LANGUAGES = [
    ('fr-be', _('French')),
    ('en', _('English')),
]

TIME_ZONE = 'Europe/Brussels'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.8/howto/static-files/
STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, "uploads")
MEDIA_URL = '/media/'

CONTENT_TYPES = ['application/csv', 'application/doc', 'application/pdf', 'application/xls', 'application/xml',
                 'application/zip', 'image/jpeg', 'image/gif', 'image/png', 'text/html', 'text/plain']
MAX_UPLOAD_SIZE = 5242880

# Authentication settings
LOGIN_REDIRECT_URL = 'home'
LOGIN_URL = 'login'

FIXTURE_DIRS = (
    '/base/fixtures/',
)

LOCALE_PATHS = ()

MESSAGE_STORAGE = 'django.contrib.messages.storage.fallback.FallbackStorage'

EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = os.path.join(BASE_DIR, "base/tests/sent_mails")

DEFAULT_FROM_EMAIL = 'osis@localhost.be'
SERVER_EMAIL = DEFAULT_FROM_EMAIL

SCREEN_SHOT_FOLDER = os.path.join(BASE_DIR, "base/tests/selenium/screenshots")
FIREFOX_PROFILE_PATH = os.path.join(BASE_DIR, "base/tests/selenium/firefox_profile")
JENKINS_TASKS = []

EMAIL_PRODUCTION_SENDING = False
COMMON_EMAIL_RECEIVER = 'osis@localhost.org'

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            {'name': 'basicstyles', 'items': ['Bold', 'Italic', 'Underline', 'Strike', '-', 'RemoveFormat']},
            {'name': 'links', 'items': ['Link']},
            {'name': 'styles', 'items': ['Styles', 'Format', 'Font', 'FontSize', 'Source']},
            {'name': 'colors', 'items': ['TextColor', 'BGColor']},
            '/',
            {'name': 'insert', 'items': ['Table']},
            {'name': 'paragraph',
             'items': ['NumberedList', 'BulletedList', '-', 'Outdent', 'Indent', '-', 'Blockquote', 'CreateDiv', '-',
                       'JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock']},
            {'name': 'forms',
             'items': ['Form', 'Checkbox', 'Radio', 'TextField', 'Textarea', 'Select', 'Button', 'ImageButton',
                       'HiddenField']},
            {'name': 'about', 'items': ['About']},
        ],
    },
}


# Queues Definition
# Uncomment the configuration if you want to use the queue system
# The queue system uses RabbitMq queues to communicate with other application (ex : osis)
QUEUES = {
     'QUEUE_URL': os.environ.get("RABBITMQ_HOST") or 'localhost',
     'QUEUE_USER': os.environ.get("RABBITMQ_USER") or 'guest',
     'QUEUE_PASSWORD': os.environ.get("RABBITMQ_PASSWORD") or 'guest',
     'QUEUE_PORT': 5672,
     'QUEUE_CONTEXT_ROOT': '/',
     'QUEUES_NAME': {
         'MIGRATIONS_TO_PRODUCE': 'osis_portal',
         'MIGRATIONS_TO_CONSUME': 'osis',
         'PAPER_SHEET': 'paper_sheet',
         'PERFORMANCE': 'performance'
     }
}

ENVIRONMENT = 'LOCAL'

# This has to be replaced by the actual url where you institution logo can be found.
# The best choici is to set an external url.
# Ex : LOGO_INSTITUTION_URL = 'https://www.google.be/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png'
# A relative URL will work on local , but not out of the box on the servers.
LOGO_INSTITUTION_URL = os.path.join(BASE_DIR, "base/static/img/logo_institution.jpg")

# Those urls have to be provided to be used for the emails signature templating.
LOGO_EMAIL_SIGNATURE_URL = ''
LOGO_OSIS_URL = ''


try:
    from backoffice.server_settings import *

    try:
        INSTALLED_APPS = INSTALLED_APPS + SERVER_APPS
        LOCALE_PATHS = LOCALE_PATHS + SERVER_LOCALE_PATHS
    except NameError:
        pass
except ImportError:
    pass
