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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.test import TestCase

from education_group.contrib.models import EducationGroupRoleModel, EducationGroupYearRoleModel


class TestEducationGroupRoleModel(TestCase):
    def test_ensure_class_is_abstract(self):
        instance = EducationGroupRoleModel()
        self.assertTrue(instance._meta.abstract)

    def test_unique_together_person_entity(self):
        instance = EducationGroupRoleModel()
        self.assertEqual(instance._meta.unique_together, (('person', 'education_group'),))


class TestEducationGroupYearRoleModel(TestCase):
    def test_ensure_class_is_abstract(self):
        instance = EducationGroupYearRoleModel()
        self.assertTrue(instance._meta.abstract)

    def test_unique_together_person_entity(self):
        instance = EducationGroupYearRoleModel()
        self.assertEqual(instance._meta.unique_together, (('person', 'education_group_year'),))
