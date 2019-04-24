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
from django.contrib.auth.models import Permission
from django.http import HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, TrainingFactory, GroupFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory, LearningUnitYearFakerFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory
from base.tests.factories.prerequisite import PrerequisiteFactory
from base.tests.factories.user import UserFactory


class TestDetail(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        cls.person = PersonFactory()
        cls.education_group_year_1 = EducationGroupYearFactory(title_english="", academic_year=cls.academic_year)
        cls.education_group_year_2 = EducationGroupYearFactory(title_english="", academic_year=cls.academic_year)
        cls.education_group_year_3 = EducationGroupYearFactory(title_english="", academic_year=cls.academic_year)
        cls.learning_unit_year_1 = LearningUnitYearFactory(specific_title_english="")
        cls.learning_unit_year_2 = LearningUnitYearFactory(specific_title_english="")
        cls.learning_component_year_1 = LearningComponentYearFactory(
            learning_unit_year=cls.learning_unit_year_1, hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=10)
        cls.learning_component_year_2 = LearningComponentYearFactory(
            learning_unit_year=cls.learning_unit_year_1, hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=10)
        cls.group_element_year_1 = GroupElementYearFactory(parent=cls.education_group_year_1,
                                                           child_branch=cls.education_group_year_2)
        cls.group_element_year_2 = GroupElementYearFactory(parent=cls.education_group_year_2,
                                                           child_branch=None,
                                                           child_leaf=cls.learning_unit_year_1)
        cls.group_element_year_3 = GroupElementYearFactory(parent=cls.education_group_year_1,
                                                           child_branch=cls.education_group_year_3)
        cls.group_element_year_4 = GroupElementYearFactory(parent=cls.education_group_year_3,
                                                           child_branch=None,
                                                           child_leaf=cls.learning_unit_year_2)
        cls.user = UserFactory()
        cls.person = PersonFactory(user=cls.user)
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))

        cls.url = reverse(
            "learning_unit_utilization",
            args=[
                cls.education_group_year_1.id,
                cls.learning_unit_year_1.id,
            ]
        )

    def test_education_group_using_template_use(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'education_group/learning_unit/tab_utilization.html')

    def test_education_group_using_check_parent_list_with_group(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(list(response.context_data['group_element_years']),
                         [self.group_element_year_2])


class TestLearningUnitPrerequisite(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        cls.education_group_year_parents = [TrainingFactory(academic_year=cls.academic_year) for _ in range(0, 2)]
        cls.learning_unit_year_child = LearningUnitYearFakerFactory(
            learning_container_year__academic_year=cls.academic_year
        )
        cls.group_element_years = [
            GroupElementYearFactory(parent=cls.education_group_year_parents[i],
                                    child_leaf=cls.learning_unit_year_child,
                                    child_branch=None)
            for i in range(0, 2)
            ]

        cls.prerequisite = PrerequisiteFactory(
            learning_unit_year=cls.learning_unit_year_child,
            education_group_year=cls.education_group_year_parents[0]
        )
        cls.person = PersonWithPermissionsFactory("can_access_education_group")
        cls.url = reverse("learning_unit_prerequisite",
                          args=[cls.education_group_year_parents[0].id, cls.learning_unit_year_child.id])

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_permission_denied_when_no_permission(self):
        person_without_permission = PersonFactory()
        self.client.force_login(person_without_permission.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "education_group/learning_unit/tab_prerequisite_training.html")

    def test_template_used_when_root_is_not_a_training(self):
        education_group_year_group = GroupFactory(academic_year=self.academic_year)
        GroupElementYearFactory(parent=self.education_group_year_parents[0],
                                child_branch=education_group_year_group)
        GroupElementYearFactory(parent=education_group_year_group,
                                child_leaf=self.learning_unit_year_child,
                                child_branch=None)

        url = reverse("learning_unit_prerequisite",
                      args=[education_group_year_group.id, self.learning_unit_year_child.id])

        response = self.client.get(url)
        self.assertTemplateUsed(response, "education_group/learning_unit/tab_prerequisite_group.html")

    def test_context_data(self):
        response = self.client.get(self.url)

        actual_prerequisites = response.context_data["prerequisite"]
        self.assertEqual(actual_prerequisites, self.prerequisite)

    def test_context_data_when_education_group_year_root_is_not_a_training(self):
        education_group_year_group = GroupFactory(academic_year=self.academic_year)
        GroupElementYearFactory(parent=self.education_group_year_parents[0],
                                child_branch=education_group_year_group)
        GroupElementYearFactory(parent=education_group_year_group,
                                child_leaf=self.learning_unit_year_child,
                                child_branch=None)

        url = reverse("learning_unit_prerequisite",
                      args=[education_group_year_group.id, self.learning_unit_year_child.id])

        response = self.client.get(url)
        self.assertCountEqual(response.context_data["formations"], self.education_group_year_parents)

        actual_prerequisites = next(filter(lambda egy: egy.id == self.education_group_year_parents[0].id,
                                           response.context_data["formations"])).prerequisites
        self.assertEqual(actual_prerequisites, [self.prerequisite])

        actual_prerequisites = next(filter(lambda egy: egy.id == self.education_group_year_parents[1].id,
                                           response.context_data["formations"])).prerequisites
        self.assertEqual(actual_prerequisites, [])