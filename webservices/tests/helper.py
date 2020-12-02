##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
import json

from django.urls import reverse
from rest_framework.test import APIClient

from base.tests.factories.user import UserFactory


class Helper:
    def _get_url(self, year, language, acronym):
        return reverse(self.URL_NAME,
                       kwargs=dict(year=year, language=language, acronym=acronym))

    def _get_response(self, year, language, acronym):
        return self.client.get(self._get_url(year, language, acronym), format='json')

    def post(self, year, language, acronym, data):
        client = APIClient()
        client.force_authenticate(UserFactory())
        return client.post(self._get_url(year, language, acronym),
                                data=json.dumps(data),
                                content_type='application/json')