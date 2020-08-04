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
from django.utils.translation import gettext as _

from base.tests.factories.academic_year import AcademicYearFactory
from education_group.models.group_year import GroupYear
from education_group.tests.factories.group import GroupFactory
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory


class TestGroupYear(TestCase):
    def test_str(self):
        group = GroupFactory()
        group_yr = GroupYearFactory(group=group, academic_year=group.start_year)
        self.assertEqual(str(group_yr),
                         "{} ({})".format(group_yr.acronym,
                                          group_yr.academic_year))

    def test_complete_title(self):
        group_year = GroupYearFactory()
        self.assertEqual(group_year.complete_title, group_year.title_fr)


class TestGroupYearSave(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year_2019 = AcademicYearFactory(year=2019)
        cls.academic_year_2023 = AcademicYearFactory(year=2023)

        cls.academic_year_less = AcademicYearFactory(year=cls.academic_year_2019.year - 1)
        cls.academic_year_greater = AcademicYearFactory(year=cls.academic_year_2023.year + 1)

        cls.group_2019_2023 = GroupFactory(start_year=cls.academic_year_2019,
                                           end_year=cls.academic_year_2023)
        cls.group_without_end_year = GroupFactory(start_year=cls.academic_year_2019,
                                                  end_year=None)

    def test_save_case_academic_year_less_than_start_year_error(self):
        with self.assertRaisesMessage(
                AttributeError,
                _('Please enter an academic year greater or equal to group start year.')):
            group_yr = GroupYearFactory(
                group=self.group_2019_2023,
                academic_year=self.academic_year_less
            )
            group_yr.save()
            self.assertFalse(
                GroupYear.objects.filter(group=self.group_2019_2023, academic_year=self.academic_year_less).exists()
            )

    def test_save_case_academic_year_greater_than_end_year_error(self):
        with self.assertRaisesMessage(
                AttributeError,
                _('Please enter an academic year less or equal to group end year.')):
            group_yr = GroupYearFactory(
                group=self.group_2019_2023,
                academic_year=self.academic_year_greater
            )
            group_yr.save()
            self.assertFalse(
                GroupYear.objects.filter(group=self.group_2019_2023, academic_year=self.academic_year_greater).exists()
            )

    def test_save_case_academic_year_no_check_on_end_year(self):
        group_yr = GroupYearFactory(
            group=self.group_without_end_year,
            academic_year=self.academic_year_greater
        )
        group_yr.save()
        self.assertTrue(
            GroupYear.objects.filter(group=self.group_without_end_year,
                                     academic_year=self.academic_year_greater).exists()
        )


class TestGroupYearVersionManager(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year_2019 = AcademicYearFactory(year=2019)
        cls.group = GroupFactory(start_year=cls.academic_year_2019, end_year=cls.academic_year_2019)

    def test_without_education_group_version(self):
        GroupYearFactory(
            group=self.group,
            academic_year=self.academic_year_2019
        )
        self.assertListEqual(list(GroupYear.objects_version.all()), [])

    def test_with_education_group_version(self):
        group_yr_2 = GroupYearFactory(
            group=self.group,
            academic_year=self.academic_year_2019
        )
        EducationGroupVersionFactory(root_group=group_yr_2)
        self.assertListEqual(list(GroupYear.objects_version.all()), [group_yr_2])
