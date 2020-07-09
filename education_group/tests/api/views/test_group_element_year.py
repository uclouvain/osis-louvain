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
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from base.models.enums.education_group_types import GroupType, TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import TrainingFactory, GroupFactory, MiniTrainingFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from education_group.api.serializers.group_element_year import EducationGroupRootNodeTreeSerializer
from education_group.api.views.group_element_year import TrainingTreeView, GroupTreeView, MiniTrainingTreeView
from program_management.ddd.domain.link import Link
from program_management.ddd.repositories import load_tree


class TrainingTreeViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """
            DROI2M
            |--Common Core
               |-- Learning unit year
            |--Finality list choice
               |-- DROI2MS/IU
                  |--Common core
        """
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.training = TrainingFactory(
            acronym='DROI2M',
            partial_acronym='LBROI200M',
            academic_year=cls.academic_year,
            education_group_type__name=TrainingType.PGRM_MASTER_120.name
        )
        cls.common_core = GroupFactory(
            education_group_type__name=GroupType.COMMON_CORE.name,
            academic_year=cls.academic_year
        )
        GroupElementYearFactory(parent=cls.training, child_branch=cls.common_core, child_leaf=None)

        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=cls.academic_year,
            learning_container_year__academic_year=cls.academic_year
        )
        GroupElementYearFactory(parent=cls.common_core, child_branch=None, child_leaf=cls.learning_unit_year)

        cls.finality_list_choice = GroupFactory(
            education_group_type__name=GroupType.FINALITY_120_LIST_CHOICE.name,
            academic_year=cls.academic_year
        )
        GroupElementYearFactory(parent=cls.training, child_branch=cls.finality_list_choice, child_leaf=None)
        cls.training_ms = TrainingFactory(
            acronym='DROI2MS/IU',
            partial_acronym='LIURE200S',
            academic_year=cls.academic_year,
            education_group_type__name=TrainingType.MASTER_MS_120.name
        )
        GroupElementYearFactory(parent=cls.finality_list_choice, child_branch=cls.training_ms, child_leaf=None)
        cls.common_core_ms = GroupFactory(
            education_group_type__name=GroupType.COMMON_CORE.name,
            academic_year=cls.academic_year
        )
        GroupElementYearFactory(parent=cls.training_ms, child_branch=cls.common_core_ms, child_leaf=None)
        cls.person = PersonFactory()
        url_kwargs = {
            'acronym': cls.training.acronym,
            'year': cls.training.academic_year.year
        }
        cls.url = reverse('education_group_api_v1:' + TrainingTreeView.name, kwargs=url_kwargs)

    def setUp(self):
        self.client.force_authenticate(user=self.person.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_training_not_found(self):
        invalid_url = reverse(
            'education_group_api_v1:' + TrainingTreeView.name,
            kwargs={'acronym': 'AGRO2M', 'year': 2019}
        )
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_training_tree(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=load_tree.load(self.training.id).root_node),
            context={
                'request': RequestFactory().get(self.url),
            }
        )
        self.assertEqual(response.data, serializer.data)

    def test_get_result_with_lowercase_acronym(self):
        url_kwargs = {
            'acronym': self.training.acronym.lower(),
            'year': self.training.academic_year.year
        }
        url = reverse('education_group_api_v1:' + TrainingTreeView.name, kwargs=url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class MiniTrainingTreeViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """
        |LBIOL212O - Cours au choix
        |--Common Core
               |-- Learning unit year
        """
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.mini_training = MiniTrainingFactory(
            acronym="CCHOIXM60",
            partial_acronym='LBIOL212O',
            academic_year=cls.academic_year
        )
        cls.common_core = GroupFactory(
            education_group_type__name=GroupType.COMMON_CORE.name,
            academic_year=cls.academic_year
        )
        GroupElementYearFactory(parent=cls.mini_training, child_branch=cls.common_core, child_leaf=None)
        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=cls.academic_year,
            learning_container_year__academic_year=cls.academic_year
        )
        GroupElementYearFactory(parent=cls.common_core, child_branch=None, child_leaf=cls.learning_unit_year)

        cls.person = PersonFactory()
        url_kwargs = {
            'partial_acronym': cls.mini_training.partial_acronym,
            'year': cls.mini_training.academic_year.year
        }
        cls.url = reverse('education_group_api_v1:' + MiniTrainingTreeView.name, kwargs=url_kwargs)

    def setUp(self):
        self.client.force_authenticate(user=self.person.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_mini_training_not_found(self):
        invalid_url = reverse(
            'education_group_api_v1:' + MiniTrainingTreeView.name,
            kwargs={'partial_acronym': 'LDROI100O', 'year': 2018}
        )
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_mini_training_tree(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=load_tree.load(self.mini_training.id).root_node),
            context={
                'request': RequestFactory().get(self.url),
            }
        )
        self.assertEqual(response.data, serializer.data)

    def test_get_result_with_lowercase_acronym(self):
        url_kwargs = {
            'partial_acronym': self.mini_training.partial_acronym.lower(),
            'year': self.mini_training.academic_year.year
        }
        url = reverse('education_group_api_v1:' + MiniTrainingTreeView.name, kwargs=url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GroupTreeViewTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """
        |--Common Core
               |-- Learning unit year
               |-- Sub group
        """
        cls.academic_year = AcademicYearFactory(year=2018)
        cls.common_core = GroupFactory(
            education_group_type__name=GroupType.COMMON_CORE.name,
            academic_year=cls.academic_year
        )
        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=cls.academic_year,
            learning_container_year__academic_year=cls.academic_year
        )
        GroupElementYearFactory(parent=cls.common_core, child_branch=None, child_leaf=cls.learning_unit_year)
        cls.sub_group = GroupFactory(
            education_group_type__name=GroupType.SUB_GROUP.name,
            academic_year=cls.academic_year
        )
        GroupElementYearFactory(parent=cls.common_core, child_branch=cls.sub_group, child_leaf=None)
        cls.person = PersonFactory()
        url_kwargs = {
            'partial_acronym': cls.common_core.partial_acronym,
            'year': cls.common_core.academic_year.year
        }
        cls.url = reverse('education_group_api_v1:' + GroupTreeView.name, kwargs=url_kwargs)

    def setUp(self):
        self.client.force_authenticate(user=self.person.user)

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_group_not_found(self):
        invalid_url = reverse(
            'education_group_api_v1:' + GroupTreeView.name,
            kwargs={'partial_acronym': 'LDROI100G', 'year': 2018}
        )
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_group_tree(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = EducationGroupRootNodeTreeSerializer(
            Link(parent=None, child=load_tree.load(self.common_core.id).root_node),
            context={
                'request': RequestFactory().get(self.url),
            }
        )
        self.assertEqual(response.data, serializer.data)

    def test_get_result_with_lowercase_acronym(self):
        url_kwargs = {
            'partial_acronym': self.common_core.partial_acronym.lower(),
            'year': self.common_core.academic_year.year
        }
        url = reverse('education_group_api_v1:' + GroupTreeView.name, kwargs=url_kwargs)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
