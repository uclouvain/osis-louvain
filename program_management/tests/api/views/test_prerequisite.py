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

from django.test import RequestFactory, override_settings
from django.urls import reverse
from mock import patch
from rest_framework import status
from rest_framework.test import APITestCase

from base.models.enums import prerequisite_operator, education_group_categories
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.person import PersonFactory
from program_management.api.serializers.prerequisite import ProgramTreePrerequisitesSerializer
from program_management.ddd.domain import prerequisite
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory


@override_settings(LANGUAGES=[('fr', 'Français'), ], LANGUAGE_CODE='fr')
class ProgramTreePrerequisitesBaseTestCase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        """
        root_node
        |-----common_core
             |---- LDROI100A (UE) Prerequisites: LDROI1300 AND LAGRO2400
        |----subgroup1
             |---- LDROI120B (UE)
             |----subgroup2
                  |---- LDROI1300 (UE)
                  |---- LAGRO2400 (UE)
        :return:
        """
        cls.person = PersonFactory()
        cls.root_node = NodeGroupYearFactory(node_id=1, code="LBIR100B", title="Bachelier en droit", year=2018)
        cls.common_core = NodeGroupYearFactory(node_id=2, code="LGROUP100A", title="Tronc commun", year=2018)
        cls.ldroi100a = NodeLearningUnitYearFactory(node_id=3,
                                                    code="LDROI100A",
                                                    common_title_fr="Introduction",
                                                    specific_title_fr="Partie 1",
                                                    year=2018)
        cls.ldroi120b = NodeLearningUnitYearFactory(node_id=4,
                                                    code="LDROI120B",
                                                    common_title_fr="Séminaire",
                                                    specific_title_fr="Partie 1",
                                                    year=2018)
        cls.subgroup1 = NodeGroupYearFactory(node_id=5, code="LSUBGR100G", title="Sous-groupe 1", year=2018)
        cls.subgroup2 = NodeGroupYearFactory(node_id=10, code="LSUBGR190G", title="Sous-groupe 2", year=2018)

        cls.ldroi1300 = NodeLearningUnitYearFactory(node_id=7,
                                                    code="LDROI1300",
                                                    common_title_fr="Introduction droit",
                                                    specific_title_fr="Partie 1",
                                                    year=2018)
        cls.lagro2400 = NodeLearningUnitYearFactory(node_id=8,
                                                    code="LAGRO2400",
                                                    common_title_fr="Séminaire agro",
                                                    specific_title_fr="Partie 1",
                                                    year=2018)

        LinkFactory(parent=cls.root_node, child=cls.common_core)
        LinkFactory(parent=cls.common_core, child=cls.ldroi100a)
        LinkFactory(parent=cls.root_node, child=cls.subgroup1)
        LinkFactory(parent=cls.subgroup1, child=cls.ldroi120b)
        LinkFactory(parent=cls.subgroup1, child=cls.subgroup2)
        LinkFactory(parent=cls.subgroup2, child=cls.ldroi1300)
        LinkFactory(parent=cls.subgroup2, child=cls.lagro2400)

        cls.p_group = prerequisite.PrerequisiteItemGroup(operator=prerequisite_operator.AND)
        cls.p_group.add_prerequisite_item('LDROI1300', 2018)
        cls.p_group.add_prerequisite_item('LAGRO2400', 2018)

        p_req = prerequisite.Prerequisite(main_operator=prerequisite_operator.AND)
        p_req.add_prerequisite_item_group(cls.p_group)
        cls.ldroi100a.set_prerequisite(p_req)

        cls.tree = ProgramTree(root_node=cls.root_node)

    def setUp(self):
        self.client.force_authenticate(user=self.person.user)


@override_settings(LANGUAGES=[('fr', 'Français'), ], LANGUAGE_CODE='fr')
class TrainingPrerequisitesTestCase(ProgramTreePrerequisitesBaseTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.root_egy = EducationGroupYearFactory(id=cls.root_node.node_id,
                                                 education_group_type__category=education_group_categories.TRAINING,
                                                 acronym=cls.root_node.code,
                                                 title=cls.root_node.title,
                                                 academic_year__year=cls.root_node.year)
        cls.egv_root = EducationGroupVersionFactory(offer=cls.root_egy,
                                                    version_name='')

        cls.url = reverse('program_management_api_v1:training-prerequisites_official',
                          kwargs={'year': cls.root_node.year, 'acronym': cls.root_node.code})
        cls.request = RequestFactory().get(cls.url)
        cls.serializer = ProgramTreePrerequisitesSerializer(cls.ldroi100a, context={
            'request': cls.request,
            'language': 'fr',
            'tree': cls.tree
        })

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            with self.subTest(method):
                response = getattr(self.client, method)(self.url)
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_results_case_training_not_found(self):
        invalid_url = reverse('program_management_api_v1:training-prerequisites_official',
                              kwargs={'acronym': 'ACRO', 'year': 2019})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('program_management.api.views.prerequisite.TrainingPrerequisites.get_tree')
    def test_get_results(self, mock_tree):
        mock_tree.return_value = self.tree
        response = self.client.get(self.url)
        with self.subTest('Test status code'):
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.subTest('Test response'):
            self.assertEqual(response.data, [self.serializer.data])


@override_settings(LANGUAGES=[('fr', 'Français'), ], LANGUAGE_CODE='fr')
class MiniTrainingPrerequisitesTestCase(ProgramTreePrerequisitesBaseTestCase):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()

        cls.root_egy = EducationGroupYearFactory(id=cls.root_node.node_id,
                                                 education_group_type__category=
                                                 education_group_categories.MINI_TRAINING,
                                                 partial_acronym=cls.root_node.code,
                                                 title=cls.root_node.title,
                                                 academic_year__year=cls.root_node.year)

        cls.egv_root = EducationGroupVersionFactory(offer=cls.root_egy,
                                                    version_name='')

        cls.url = reverse('program_management_api_v1:mini_training-prerequisites_official',
                          kwargs={'year': cls.root_node.year, 'partial_acronym': cls.root_node.code})
        cls.request = RequestFactory().get(cls.url)
        cls.serializer = ProgramTreePrerequisitesSerializer(cls.ldroi100a, context={
            'request': cls.request,
            'language': 'fr',
            'tree': cls.tree
        })

    def test_get_not_authorized(self):
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_method_not_allowed(self):
        methods_not_allowed = ['post', 'delete', 'put', 'patch']

        for method in methods_not_allowed:
            with self.subTest(method):
                response = getattr(self.client, method)(self.url)
                self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_get_results_case_mini_training_not_found(self):
        invalid_url = reverse('program_management_api_v1:mini_training-prerequisites_official',
                              kwargs={'partial_acronym': 'ACRO', 'year': 2019})
        response = self.client.get(invalid_url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('program_management.api.views.prerequisite.MiniTrainingPrerequisites.get_tree')
    def test_get_results(self, mock_tree):
        mock_tree.return_value = self.tree
        response = self.client.get(self.url)
        with self.subTest('Test status code'):
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        with self.subTest('Test response'):
            self.assertEqual(response.data, [self.serializer.data])
