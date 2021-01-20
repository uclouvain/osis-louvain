#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase
from django.urls import reverse

from base.models.admission_condition import AdmissionConditionLine, CONDITION_ADMISSION_ACCESSES
from base.tests.factories.person import SuperUserPersonFactory
from education_group.tests.views.admission_condition.common import TestAdmissionConditionMixin


class TestCreateAdmissionConditionLine(TestCase, TestAdmissionConditionMixin):
    @classmethod
    def setUpTestData(cls):
        cls.person = SuperUserPersonFactory()

    def setUp(self) -> None:
        self.generate_condition_line_data()

        self.en_url = reverse(
            "education_group_year_admission_condition_create_line",
            args=[self.education_group_year.academic_year.year, self.education_group_year.partial_acronym]
        ) + "?section={}&language=en".format(self.LINE_SECTION)
        self.fr_url = reverse(
            "education_group_year_admission_condition_create_line",
            args=[self.education_group_year.academic_year.year, self.education_group_year.partial_acronym]
        ) + "?section={}&language=fr".format(self.LINE_SECTION)
        self.client.force_login(self.person.user)

    def test_success_post_should_create_achievement(self):
        count_before_create = AdmissionConditionLine.objects.filter(
            admission_condition=self.admission_condition
        ).count()

        response = self.client.post(self.fr_url, data=self.generate_fr_post_data())
        response = self.client.post(self.en_url, data=self.generate_en_post_data())

        self.assertEqual(
            AdmissionConditionLine.objects.filter(admission_condition=self.admission_condition).count(),
            count_before_create + 2
        )

    def test_postpone_should_overwrite_next_years_data(self):
        self.client.post(self.fr_url, data=self.generate_fr_post_data(to_postpone=True))

        self.assert_conditions_line_equal(self.education_group_year, self.next_year_education_group_year, self.SECTION)

    @classmethod
    def generate_fr_post_data(cls, to_postpone=False):
        post_data = {
            "section": cls.LINE_SECTION,
            "access": CONDITION_ADMISSION_ACCESSES[0][0],
            "conditions": "Conditions",
            "remarks": "test test",
            "diploma": "bachelor"
        }
        if to_postpone:
            post_data["to_postpone"] = "1"
        return post_data

    @classmethod
    def generate_en_post_data(cls, to_postpone=False):
        post_data = {
            "section": cls.LINE_SECTION,
            "access": CONDITION_ADMISSION_ACCESSES[0][0],
            "conditions_en": "Conditions",
            "remarks_en": "test test",
            "diploma_en": "bachelor"
        }
        if to_postpone:
            post_data["to_postpone"] = "1"
        return post_data

