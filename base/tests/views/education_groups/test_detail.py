##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.models.enums.education_group_categories import TRAINING
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.education_group_year import EducationGroupYearFactory, TrainingFactory, GroupFactory, \
    MiniTrainingFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_unit_component import LearningUnitComponentFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory


class TestReadEducationGroup(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.person = PersonFactory(user=cls.user)
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))

    def test_training_template_used(self):
        training = TrainingFactory()
        url = reverse("education_group_read", args=[training.pk, training.pk])
        expected_template = "education_group/identification_training_details.html"

        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertTemplateUsed(response, expected_template)

    def test_mini_training_template_used(self):
        mini_training = MiniTrainingFactory()
        url = reverse("education_group_read", args=[mini_training.pk, mini_training.pk])
        expected_template = "education_group/identification_mini_training_details.html"

        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertTemplateUsed(response, expected_template)

    def test_group_template_used(self):
        group = GroupFactory()
        url = reverse("education_group_read", args=[group.pk, group.pk])
        expected_template = "education_group/identification_group_details.html"

        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertTemplateUsed(response, expected_template)

    def test_show_coorganization_case_not_2m(self):
        training_not_2m = EducationGroupYearFactory(
            education_group_type__category=TRAINING,
            education_group_type__name=TrainingType.CAPAES.name
        )
        url = reverse("education_group_read", args=[training_not_2m.pk, training_not_2m.pk])
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertTrue(response.context['show_coorganization'])

    def test_show_coorganization_case_2m(self):
        training_2m = EducationGroupYearFactory(
            education_group_type__category=TRAINING,
            education_group_type__name=TrainingType.PGRM_MASTER_120.name
        )
        url = reverse("education_group_read", args=[training_2m.pk, training_2m.pk])
        self.client.force_login(self.user)
        response = self.client.get(url)
        self.assertFalse(response.context['show_coorganization'])


class TestUtilizationTab(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person = PersonFactory()
        cls.education_group_year_1 = EducationGroupYearFactory(title_english="")
        cls.education_group_year_2 = EducationGroupYearFactory(title_english="")
        cls.education_group_year_3 = EducationGroupYearFactory(title_english="")
        cls.learning_unit_year_1 = LearningUnitYearFactory(specific_title_english="")
        cls.learning_unit_year_2 = LearningUnitYearFactory(specific_title_english="")
        cls.learning_component_year_1 = LearningComponentYearFactory(
            learning_container_year=cls.learning_unit_year_1.learning_container_year, hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=10)
        cls.learning_component_year_2 = LearningComponentYearFactory(
            learning_container_year=cls.learning_unit_year_1.learning_container_year, hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=10)
        cls.learning_unit_component_1 = LearningUnitComponentFactory(
            learning_component_year=cls.learning_component_year_1,
            learning_unit_year=cls.learning_unit_year_1)
        cls.learning_unit_component_2 = LearningUnitComponentFactory(
            learning_component_year=cls.learning_component_year_2,
            learning_unit_year=cls.learning_unit_year_1)
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
            "education_group_utilization",
            args=[
                cls.education_group_year_2.id,
                cls.education_group_year_2.id,
            ]
        )

    def test_education_group_using_template_use(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'education_group/tab_utilization.html')

    def test_education_group_using_check_parent_list_with_group(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(len(response.context_data['group_element_years']), 1)
        self.assertTemplateUsed(response, 'education_group/tab_utilization.html')


class TestContent(TestCase):
    def setUp(self):
        self.person = PersonFactory()
        self.education_group_year_1 = EducationGroupYearFactory()
        self.education_group_year_2 = EducationGroupYearFactory()
        self.education_group_year_3 = EducationGroupYearFactory()
        self.learning_unit_year_1 = LearningUnitYearFactory()

        self.learning_component_year_1 = LearningComponentYearFactory(
            learning_container_year=self.learning_unit_year_1.learning_container_year,
            hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=10
        )

        self.learning_component_year_2 = LearningComponentYearFactory(
            learning_container_year=self.learning_unit_year_1.learning_container_year,
            hourly_volume_partial_q1=10,
            hourly_volume_partial_q2=10
        )

        self.learning_unit_component_1 = LearningUnitComponentFactory(
            learning_component_year=self.learning_component_year_1,
            learning_unit_year=self.learning_unit_year_1
        )

        self.learning_unit_component_2 = LearningUnitComponentFactory(
            learning_component_year=self.learning_component_year_2,
            learning_unit_year=self.learning_unit_year_1
        )

        self.learning_unit_year_without_container = LearningUnitYearFactory(
            learning_container_year=None
        )

        self.group_element_year_1 = GroupElementYearFactory(parent=self.education_group_year_1,
                                                            child_branch=self.education_group_year_2)

        self.group_element_year_2 = GroupElementYearFactory(parent=self.education_group_year_1,
                                                            child_branch=None,
                                                            child_leaf=self.learning_unit_year_1)

        self.group_element_year_3 = GroupElementYearFactory(parent=self.education_group_year_1,
                                                            child_branch=self.education_group_year_3)

        self.group_element_year_without_container = GroupElementYearFactory(
            parent=self.education_group_year_1,
            child_branch=None,
            child_leaf=self.learning_unit_year_without_container
        )

        self.user = UserFactory()
        self.person = PersonFactory(user=self.user)
        self.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))

        self.url = reverse(
            "education_group_content",
            args=[
                self.education_group_year_1.id,
                self.education_group_year_1.id,
            ]
        )
        self.client.force_login(self.user)

    def test_context(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "education_group/tab_content.html")

        geys = response.context["group_element_years"]
        self.assertIn(self.group_element_year_1, geys)
        self.assertIn(self.group_element_year_2, geys)
        self.assertIn(self.group_element_year_3, geys)
        self.assertNotIn(self.group_element_year_without_container, geys)
