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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

from django.core.exceptions import ValidationError
from django.test import TestCase

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import GroupFactory
from education_group.models.group import Group
from education_group.tests.factories.group import GroupFactory


class TestGroupSave(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.academic_year_1999 = AcademicYearFactory(year=1999)
        cls.academic_year_2000 = AcademicYearFactory(year=2000)

    def test_save_case_start_year_greater_than_end_year_error(self):
        group = GroupFactory.build(
            start_year=self.academic_year_2000,
            end_year=self.academic_year_1999
        )
        with self.assertRaises(AttributeError):
            group.save()
            self.assertFalse(
                Group.objects.get(start_year=self.academic_year_2000, end_year=self.academic_year_1999).exists()
            )

    def test_save_case_start_year_equals_to_end_year_no_error(self):
        group = GroupFactory.build(
            start_year=self.academic_year_2000,
            end_year=self.academic_year_2000
        )
        group.save()

        self.assertTrue(
            Group.objects.filter(start_year=self.academic_year_2000, end_year=self.academic_year_2000).exists()
        )

    def test_save_case_start_year_lower_to_end_year_no_error(self):
        group = GroupFactory.build(
            start_year=self.academic_year_1999,
            end_year=self.academic_year_2000
        )
        group.save()

        self.assertTrue(
            Group.objects.filter(start_year=self.academic_year_1999, end_year=self.academic_year_2000).exists()
        )
