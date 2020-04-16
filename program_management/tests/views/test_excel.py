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
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.person import PersonWithPermissionsFactory
from osis_common.document.xls_build import CONTENT_TYPE_XLS


class TestGetLearningUnitExcel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonWithPermissionsFactory("view_educationgroup")
        cls.education_group_year = EducationGroupYearFactory()

        cls.url_prerequisites = reverse("education_group_learning_units_prerequisites",
                                        args=[cls.education_group_year.pk])
        cls.url_is_prerequisite = reverse("education_group_learning_units_is_prerequisite_for",
                                          args=[cls.education_group_year.pk])
        cls.url_contains = reverse("education_group_learning_units_contains",
                                   args=[cls.education_group_year.pk, cls.education_group_year.pk])

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_return_excel_file_prerequisites(self):
        response = self.client.get(self.url_prerequisites)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], CONTENT_TYPE_XLS)

    def test_return_excel_file_is_prerequisite(self):
        response = self.client.get(self.url_is_prerequisite)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], CONTENT_TYPE_XLS)

    def test_return_excel_file_contains(self):
        response = self.client.get(self.url_contains)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], CONTENT_TYPE_XLS)
        expected_filename = "{workbook_name}.xlsx".format(
            workbook_name=str(_("LearningUnitList-%(year)s-%(acronym)s") % {
                "year": self.education_group_year.academic_year.year,
                "acronym": self.education_group_year.acronym
            })
        )
        self.assertEqual(response['Content-Disposition'],
                         "attachment; filename={}".format(expected_filename))
