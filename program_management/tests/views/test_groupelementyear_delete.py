##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from waffle.testutils import override_flag

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.prerequisite_item import PrerequisiteItemFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory


@override_flag('education_group_update', active=True)
class TestDetachLearningUnitPrerequisite(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        cls.education_group_year = EducationGroupYearFactory(academic_year=cls.academic_year)
        cls.luy = LearningUnitYearFactory()
        cls.group_element_year_root = GroupElementYearFactory(
            parent__academic_year=cls.academic_year,
            child_branch=cls.education_group_year
        )
        cls.group_element_year = GroupElementYearFactory(
            parent=cls.education_group_year,
            child_branch=None,
            child_leaf=cls.luy
        )
        cls.person = CentralManagerFactory(entity=cls.education_group_year.management_entity).person
        cls.person.user.user_permissions.add(Permission.objects.get(codename="view_educationgroup"))
        cls.url = reverse("group_element_year_delete", args=[
            cls.education_group_year.id,
            cls.education_group_year.id,
            cls.group_element_year.id
        ])

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_detach_case_learning_unit_being_prerequisite(self):
        PrerequisiteItemFactory(
            prerequisite__education_group_year=self.group_element_year_root.parent,
            learning_unit=self.luy.learning_unit
        )

        response = self.client.post(self.url, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.json(), {"error": True})

    def test_detach_case_learning_unit_having_prerequisite(self):
        PrerequisiteItemFactory(
            prerequisite__learning_unit_year=self.luy,
            prerequisite__education_group_year=self.group_element_year_root.parent
        )

        response = self.client.post(self.url, follow=True, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.json(), {"error": True})
