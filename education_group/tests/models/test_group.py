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

from django.test import TestCase

from base.tests.factories.academic_year import AcademicYearFactory
from education_group.models.group import Group
from education_group.models.group_year import GroupYear
from education_group.tests.factories.group import GroupFactory
from education_group.tests.factories.group_year import GroupYearFactory


class TestGroup(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year_1 = AcademicYearFactory()
        cls.academic_year_2 = AcademicYearFactory(year=cls.academic_year_1.year+3)

    def test_most_recent_acronym_no_group_year(self):
        group = GroupFactory()
        group_in_db = Group.objects.get(pk=group.id)  # Necessary otherwise the groupyear_set collection is empty
        self.assertIsNone(group_in_db.most_recent_acronym, "")

    def test_most_recent_acronym(self):
        a_group = GroupFactory(start_year=self.academic_year_1)
        GroupYearFactory(group=a_group, academic_year=self.academic_year_1)
        most_recent_group_yr = GroupYearFactory(group=a_group, academic_year=self.academic_year_2)
        group_in_db = Group.objects.get(pk=a_group.id)  # Necessary otherwise the groupyear_set collection is empty

        self.assertEqual(group_in_db.most_recent_acronym,
                         GroupYear.objects.get(pk=most_recent_group_yr.id).acronym)


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
