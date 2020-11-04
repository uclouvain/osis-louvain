# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from education_group.ddd.domain.service.get_common_publish_url import GetCommonPublishUrl


@override_settings(
    ESB_API_URL="api.esb.com",
    ESB_REFRESH_COMMON_ADMISSION_ENDPOINT="common/{year}/refresh",
)
class TestGetCommonAdmissionConditionsPublishUrl(SimpleTestCase):
    @override_settings(ESB_REFRESH_COMMON_ADMISSION_ENDPOINT=None)
    def test_publish_case_missing_settings(self):
        with self.assertRaises(ImproperlyConfigured):
            GetCommonPublishUrl.get_url_admission_conditions(2018)

    def test_assert_common_admission_conditions_publish_url(self):
        expected_publish_url = "api.esb.com/common/2018/refresh"

        self.assertEqual(
            GetCommonPublishUrl.get_url_admission_conditions(2018),
            expected_publish_url
        )


@override_settings(
    ESB_API_URL="api.esb.com",
    ESB_REFRESH_COMMON_PEDAGOGY_ENDPOINT="common-pedagogy/{year}/refresh",
)
class TestGetCommonPedagogyPublishUrl(SimpleTestCase):
    @override_settings(ESB_REFRESH_COMMON_PEDAGOGY_ENDPOINT=None)
    def test_publish_case_missing_settings(self):
        with self.assertRaises(ImproperlyConfigured):
            GetCommonPublishUrl.get_url_pedagogy(2018)

    def test_assert_common_admission_conditions_publish_url(self):
        expected_publish_url = "api.esb.com/common-pedagogy/2018/refresh"

        self.assertEqual(
            GetCommonPublishUrl.get_url_pedagogy(2018),
            expected_publish_url
        )
