##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
import importlib
import logging

from django.conf import settings
from django.conf.urls import url, include

from webservices.api.views.auth_token import AuthToken
from webservices.api.views.common_admission_condition import CommonAdmissionCondition
from webservices.api.views.common_text import CommonText
from webservices.api.views.general_information import GeneralInformation
from webservices.api.views.user import CurrentUser

logger = logging.getLogger(settings.DEFAULT_LOGGER)

url_api_v1 = [
    url(r'^auth/token$', AuthToken.as_view(), name=AuthToken.name),
    url(r'^users/current$', CurrentUser.as_view(), name=CurrentUser.name)
]

webservice_apps = [
    'education_group',
    'learning_unit',
    'reference',
    'continuing_education',
    'base',
    'program_management',
]

for appname in webservice_apps:
    if appname in settings.INSTALLED_APPS:
        context = {'appname': appname}
        module_name = "{appname}.api.url_v1".format(**context)
        try:
            importlib.import_module(module_name)
            regex = r'^{appname}/'.format(**context)
            namespace = '{appname}_api_v1'.format(**context)

            # FIXME Add app_name for continuing_education and partnership
            url_api_v1.append(url(regex, include(module_name, namespace=namespace)))
        except ImportError:
            logger.warning('API urls from {appname} could not be imported'.format(**context))


urlpatterns = [
    url('^v0.3/catalog/offer/(?P<year>[0-9]{4})/(?P<language>[a-zA-Z]{2})/common$',
        CommonText.as_view(),
        name=CommonText.name),
    url('^v0.3/catalog/offer/(?P<year>[0-9]{4})/(?P<language>[a-zA-Z]{2})/common/admission_condition$',
        CommonAdmissionCondition.as_view(),
        name=CommonAdmissionCondition.name),
    url('^v0.3/catalog/offer/(?P<year>[0-9]{4})/(?P<language>[a-zA-Z]{2})/(?P<acronym>[a-zA-Z0-9]+)$',
        GeneralInformation.as_view(),
        name=GeneralInformation.name),
    url(r'^v1/', include(url_api_v1)),
]
