##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
import sys

from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

BASE_DIR = os.path.dirname((os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# SECURITY Settings
# Those settings are mandatory and have to be defined in your .env file
SECRET_KEY = os.environ['SECRET_KEY']
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = os.environ['ALLOWED_HOSTS'].split()
ADMIN_URL = os.environ['ADMIN_URL']
ENVIRONMENT = os.environ['ENVIRONMENT']
CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE', 'False').lower() == 'true'


# Base configuration
ROOT_URLCONF = os.environ.get('ROOT_URLCONF', 'backoffice.urls')
WSGI_APPLICATION = os.environ.get('WSGI_APPLICATION', 'backoffice.wsgi.application')
MESSAGE_STORAGE = os.environ.get('MESSAGE_STORAGE', 'django.contrib.messages.storage.fallback.FallbackStorage')


# Application definition
# Common apps for all environments
# Specific apps (all osis modules except base and reference(mandatory) + env specific apps like sentry)
# have to be defined in environment settings (ex: dev.py)
INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'analytical',
    'localflavor',
    'ckeditor',
    'osis_common',
    'reference',
    'base',
    'statici18n',
    'rest_framework',
    'rest_framework.authtoken',
    'bootstrap3',
    'ordered_model',
    'waffle',
)

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'base.middlewares.extra_http_responses_midleware.ExtraHttpResponsesMiddleware',
    'waffle.middleware.WaffleMiddleware',
)

# check if we are testing right now
TESTING = 'test' in sys.argv
if TESTING:
    # add test packages that have specific models for tests
    INSTALLED_APPS += ('osis_common.tests', )
APPS_TO_TEST = (
    'osis_common',
    'reference',
    'base',
)
TEST_RUNNER = os.environ.get('TEST_RUNNER', 'osis_common.tests.runner.InstalledAppsTestRunner')
SKIP_QUEUES_TESTS = os.environ.get('SKIP_QUEUES_TESTS', 'False').lower() == 'true'
QUEUES_TESTING_TIMEOUT = float(os.environ.get('QUEUES_TESTING_TIMEOUT', 0.1))

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'debug': DEBUG,
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.template.context_processors.i18n',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'base.views.common.common_context_processor',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get("DATABASE_NAME", 'osis_local'),
        'USER': os.environ.get("POSTGRES_USER", 'osis'),
        'PASSWORD': os.environ.get("POSTGRES_PASSWORD", 'osis'),
        'HOST': os.environ.get("POSTGRES_HOST", '127.0.0.1'),
        'PORT': os.environ.get("POSTGRES_PORT", '5432'),
        'ATOMIC_REQUESTS':  os.environ.get('DATABASE_ATOMIC_REQUEST', 'True').lower() == 'true'
    },
}

# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/
# If you want to change the default settings,
# you have to redefine the LANGUAGE_CODE and LANGUAGES vars in environment settings (ex: dev.py)
LANGUAGE_CODE = 'fr-be'
LANGUAGES = [
    ('fr-be', _('French')),
    ('en', _('English')),
]
LANGUAGE_CODE_FR = 'fr-be'
LANGUAGE_CODE_EN = 'en'
# You can change default values for internalizations settings in your .env file
USE_I18N = os.environ.get('USE_I18N', 'True').lower() == 'true'
USE_L10N = os.environ.get('USE_L10N', 'True').lower() == 'true'
USE_TZ = os.environ.get('USE_TZ', 'True').lower() == 'true'
TIME_ZONE = os.environ.get('TIME_ZONE', 'Europe/Brussels')

# Static files (CSS, JavaScript, Images) and Media
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_URL = os.environ.get('STATIC_URL', '/static/')
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', os.path.join(BASE_DIR, "uploads"))
MEDIA_URL = os.environ.get('MEDIA_URL',  '/media/')
CONTENT_TYPES = ['application/csv', 'application/doc', 'application/pdf', 'application/xls', 'application/xml',
                 'application/zip', 'image/jpeg', 'image/gif', 'image/png', 'text/html', 'text/plain']
MAX_UPLOAD_SIZE = int(os.environ.get('MAX_UPLOAD_SIZE', 5242880))

# Logging settings
# Logging framework is defined in env settings (ex: dev.py)
DEFAULT_LOGGER = os.environ.get('DEFAULT_LOGGER', 'default')
SEND_MAIL_LOGGER = os.environ.get('SEND_MAIL_LOGGER', 'send_mail')
QUEUE_EXCEPTION_LOGGER = os.environ.get('QUEUE_EXCEPTION_LOGGER', 'queue_exception')

# Email Settings
# By default Email are saved in the folder defined by EMAIL_FILE_PATH
# If you want ti use the smtp backend,
# you have to define EMAIL_BACKEND, EMAIL_HOST and EMAIL_PORT in your .env if the default values doesn't match.
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'osis@localhost.be')
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', DEFAULT_FROM_EMAIL)
LOGO_EMAIL_SIGNATURE_URL = os.environ.get('LOGO_EMAIL_SIGNATURE_URL', '')
EMAIL_PRODUCTION_SENDING = os.environ.get('EMAIL_PRODUCTION_SENDING', 'False').lower() == 'true'
COMMON_EMAIL_RECEIVER = os.environ.get('COMMON_EMAIL_RECEIVER', 'osis@localhost.org')
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', 'django.core.mail.backends.filebased.EmailBackend')
EMAIL_FILE_PATH = os.environ.get('EMAIL_FILE_PATH', os.path.join(BASE_DIR, "base/tests/sent_mails"))
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 25))
SEND_BROKEN_LINK_EMAILS = os.environ.get('SEND_BROKEN_LINK_EMAILS', 'True').lower() == 'true'
INTERNAL_EMAIL_SUFFIX = os.environ.get('INTERNAL_EMAIL_SUFFIX', 'osis.org')

# Authentication settings
LOGIN_URL = os.environ.get('LOGIN_URL', reverse_lazy('login'))
LOGIN_REDIRECT_URL = os.environ.get('LOGIN_REDIRECT_URL', reverse_lazy('home'))
LOGOUT_URL = os.environ.get('LOGOUT_URL', reverse_lazy('logout'))
OVERRIDED_LOGIN_URL = os.environ.get('OVERRIDED_LOGIN_URL', None)
OVERRIDED_LOGOUT_URL = os.environ.get('OVERRIDED_LOGOUT_URL', None)
PERSON_EXTERNAL_ID_PATTERN = os.environ.get('PERSON_EXTERNAL_ID_PATTERN', 'osis.person_{global_id}')

# Field upload settings
DATA_UPLOAD_MAX_NUMBER_FIELDS = int(os.environ.get('DATA_UPLOAD_MAX_NUMBER_FIELDS', 5000))

# This has to be set in your .env with the actual url where you institution logo can be found.
# Ex : LOGO_INSTITUTION_URL = 'https://www.google.be/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png'
# A relative URL will work on local , but not out of the box on the servers.
LOGO_INSTITUTION_URL = os.environ.get('LOGO_INSTITUTION_URL',
                                      os.path.join(BASE_DIR, "base/static/img/logo_institution.jpg"))
LOGO_OSIS_URL = os.environ.get('LOGO_OSIS_URL', '')

# The Queues are optional
# They are used to ensure the migration of Data between Osis and other application (ex : Osis <> Osis-Portal)
# See in settings.dev.example to configure the queues
QUEUES = {}

# Additionnal Locale Path
# Add local path in your environment settings (ex: dev.py)
LOCALE_PATHS = ()

# Apps Settings
CKEDITOR_JQUERY_URL = os.path.join(STATIC_URL, "js/jquery-2.1.4.min.js")
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
    'minimal': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Bold', 'Italic', 'Underline'],
            ['NumberedList', 'BulletedList'],
            ['Link', 'Unlink']
        ]
    },
    'minimal_plus_headers': {
        'toolbar': 'Custom',
        'toolbar_Custom': [
            ['Format', 'Styles'],
            ['Bold', 'Italic', 'Underline'],
            ['Link', 'Unlink'],
            ['NumberedList', 'BulletedList']
        ]
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
            'level': 'DEBUG',
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
        'send_mail': {
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

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'TEST_REQUEST_DEFAULT_FORMAT': 'json'
}

# ESB Configuration
ESB_AUTHORIZATION = os.environ.get('ESB_AUTHORIZATION')
ESB_STUDENT_API = os.environ.get('ESB_STUDENT_API')

RELEASE_TAG = os.environ.get('RELEASE_TAG')

# BOOTSTRAP3 Configuration
BOOTSTRAP3 = {
    'set_placeholder': False,
    'success_css_class': ''
}
