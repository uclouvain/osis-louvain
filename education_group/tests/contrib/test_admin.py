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
from django.test import SimpleTestCase

from education_group.contrib.admin import EducationGroupRoleModelAdmin, EducationGroupYearRoleModelAdmin


class TestEducationGroupRoleModelAdmin(SimpleTestCase):
    def test_ensure_list_display(self):
        expected_list_display = ('person', 'education_group',)
        self.assertEqual(EducationGroupRoleModelAdmin.list_display, expected_list_display)

    def test_ensure_search_fields(self):
        expected_search_fields = [
            'person__first_name',
            'person__last_name',
            'person__global_id',
            'education_group__educationgroupyear__acronym',
        ]
        self.assertListEqual(EducationGroupRoleModelAdmin.search_fields, expected_search_fields)


class TestEducationGroupYearRoleModelAdmin(SimpleTestCase):
    def test_ensure_list_display(self):
        expected_list_display = ('person', 'education_group_year',)
        self.assertEqual(EducationGroupYearRoleModelAdmin.list_display, expected_list_display)

    def test_ensure_search_fields(self):
        expected_search_fields = [
            'person__first_name',
            'person__last_name',
            'person__global_id',
            'educationgroupyear__acronym',
        ]
        self.assertListEqual(EducationGroupYearRoleModelAdmin.search_fields, expected_search_fields)
