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

from base.models.admission_condition import AdmissionConditionLine
from base.tests.factories.person import SuperUserPersonFactory
from education_group.tests.views.admission_condition.common import TestAdmissionConditionMixin


class TestDeleteAdmissionConditionLine(TestCase, TestAdmissionConditionMixin):
    @classmethod
    def setUpTestData(cls):
        cls.person = SuperUserPersonFactory()

    def setUp(self) -> None:
        self.generate_condition_line_data()

        self.url = reverse(
            "education_group_year_admission_condition_remove_line",
            args=[self.education_group_year.academic_year.year, self.education_group_year.partial_acronym]
        ) + "?id={}".format(self.admission_condition_line.id)
        self.client.force_login(self.person.user)

    def test_success_post_should_update_achievement(self):
        self.client.post(self.url, data=self.generate_post_data())

        with self.assertRaises(AdmissionConditionLine.DoesNotExist):
            AdmissionConditionLine.objects.get(id=self.admission_condition_line.id)

    def test_postpone_should_overwrite_next_years_data(self):
        self.client.post(self.url, data=self.generate_post_data(to_postpone=True))

        self.assert_conditions_line_equal(self.education_group_year, self.next_year_education_group_year, self.SECTION)

    @classmethod
    def generate_post_data(cls, to_postpone=False):
        post_data = {}
        if to_postpone:
            post_data["to_postpone"] = "1"
        return post_data

