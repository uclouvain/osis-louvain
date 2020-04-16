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
import random

from django.conf import settings
from django.http import HttpResponse
from django.test import TestCase
from django.urls import reverse
from waffle.testutils import override_flag, override_switch

from backoffice.settings.base import LANGUAGE_CODE_EN
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, EducationGroupYearBachelorFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import CentralManagerForUEFactory, PersonFactory
from base.tests.factories.user import SuperUserFactory


class TestRead(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        cls.person = PersonFactory(language=settings.LANGUAGE_CODE_FR)
        cls.education_group_year_1 = EducationGroupYearFactory(title_english="", academic_year=cls.academic_year)
        cls.education_group_year_2 = EducationGroupYearBachelorFactory(
            title_english="",
            academic_year=cls.academic_year
        )
        cls.a_superuser = SuperUserFactory()

    @override_switch('education_group_year_generate_pdf', active=True)
    def test_pdf_content(self):
        self.client.force_login(self.a_superuser)
        lang = random.choice(['fr-be', 'en'])
        url = reverse("pdf_content", args=[self.education_group_year_1.id, self.education_group_year_2.id, lang])
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'pdf_content.html')


@override_flag('pdf_content', active=True)
class TestReadPdfContent(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_year = AcademicYearFactory()
        education_group_year = EducationGroupYearFactory(academic_year=academic_year)
        GroupElementYearFactory(parent=education_group_year,
                                child_branch__academic_year=academic_year)
        cls.person = CentralManagerForUEFactory("view_educationgroup")
        cls.url = reverse(
            "group_content",
            kwargs={
                "root_id": education_group_year.id,
                "education_group_year_id": education_group_year.id
            }
        )
        cls.post_valid_data = {'action': 'Generate pdf', 'language': LANGUAGE_CODE_EN}

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_pdf_content_case_get_without_ajax_success(self):
        response = self.client.get(self.url, data=self.post_valid_data, follow=True)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "group_element_year/pdf_content.html")

    def test_pdf_content_case_get_with_ajax_success(self):
        response = self.client.get(self.url, data=self.post_valid_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "group_element_year/pdf_content_inner.html")
