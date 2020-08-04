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
from django.http import HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse

from base.models.enums.education_group_types import GroupType, TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from base.tests.factories.person import PersonFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory, ElementLearningUnitYearFactory


class TestLearningUnitUtilization(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        root_element
        |-- common code
          |--- subgroup_element
              |--- element_luy1
          |-- element_luy2
        """
        cls.academic_year = AcademicYearFactory(current=True)

        cls.root_element = ElementGroupYearFactory(
            group_year__education_group_type__name=TrainingType.BACHELOR.name,
            group_year__academic_year=cls.academic_year
        )
        cls.common_core_element = ElementGroupYearFactory(
            group_year__academic_year=cls.academic_year,
            group_year__education_group_type__name=GroupType.COMMON_CORE.name
        )
        cls.subgroup_element = ElementGroupYearFactory(
            group_year__academic_year=cls.academic_year,
            group_year__education_group_type__name=GroupType.SUB_GROUP.name
        )
        cls.element_luy1 = ElementLearningUnitYearFactory(learning_unit_year__academic_year=cls.academic_year)
        cls.element_luy2 = ElementLearningUnitYearFactory(learning_unit_year__academic_year=cls.academic_year)

        GroupElementYearFactory(parent_element=cls.root_element, child_element=cls.common_core_element)
        GroupElementYearFactory(parent_element=cls.common_core_element, child_element=cls.subgroup_element)
        GroupElementYearChildLeafFactory(parent_element=cls.common_core_element, child_element=cls.element_luy1)
        GroupElementYearChildLeafFactory(parent_element=cls.subgroup_element, child_element=cls.element_luy2)
        cls.education_group_version = EducationGroupVersionFactory(offer__academic_year=cls.academic_year,
                                                                   root_group=cls.root_element.group_year)

        cls.central_manager = CentralManagerFactory()
        cls.url = reverse(
            "learning_unit_utilization",
            kwargs={
                'root_element_id': cls.root_element.pk,
                'child_element_id': cls.element_luy1.pk,
            }
        )

    def setUp(self):
        self.client.force_login(self.central_manager.person.user)

    def test_case_when_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_when_user_has_no_permission(self):
        a_person_without_permission = PersonFactory()
        self.client.force_login(a_person_without_permission.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_assert_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'learning_unit/tab_utilization.html')

    def test_assert_key_context(self):
        response = self.client.get(self.url)

        self.assertIn('utilization_rows', response.context)
