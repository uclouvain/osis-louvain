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
from random import sample
from typing import List, Dict

from django.http import HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse

from base.models.enums.education_group_types import GroupType, TrainingType, MiniTrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from base.tests.factories.person import PersonFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.program_tree_version import STANDARD
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory, ElementLearningUnitYearFactory
from program_management.views.element_utilization import get_utilization_rows, _get_training_nodes

URL_ELEMENT_IDENTIFICATION = 'element_identification'


class TestLearningUnitUtilization(TestCase):
    @classmethod
    def setUpTestData(cls):
        """
        training_root_element
        |-- common code
          |--- subgroup_element
              |--- element_luy1
          |-- element_luy2
        |-- deepening_element
          |--- element_luy3
        """
        cls.academic_year = AcademicYearFactory(current=True)

        cls.training_root_element = ElementGroupYearFactory(
            group_year__education_group_type__name=TrainingType.BACHELOR.name,
            group_year__academic_year=cls.academic_year,
            group_year__acronym="LGEST100"
        )
        cls.common_core_element = ElementGroupYearFactory(
            group_year__academic_year=cls.academic_year,
            group_year__education_group_type__name=GroupType.COMMON_CORE.name,
            group_year__acronym="LGEST101"
        )
        cls.subgroup_element = ElementGroupYearFactory(
            group_year__academic_year=cls.academic_year,
            group_year__education_group_type__name=GroupType.SUB_GROUP.name,
            group_year__acronym="LGEST102"
        )
        cls.deepening_element = ElementGroupYearFactory(
            group_year__academic_year=cls.academic_year,
            group_year__education_group_type__name=MiniTrainingType.DEEPENING.name,
            group_year__acronym="LGEST103"
        )
        cls.deepening_subgroup_element = ElementGroupYearFactory(
            group_year__academic_year=cls.academic_year,
            group_year__education_group_type__name=GroupType.SUB_GROUP.name,
            group_year__acronym="LGEST104"
        )
        cls.element_luy1 = ElementLearningUnitYearFactory(learning_unit_year__academic_year=cls.academic_year,
                                                          learning_unit_year__acronym='FAC1')
        cls.element_luy2 = ElementLearningUnitYearFactory(learning_unit_year__academic_year=cls.academic_year,
                                                          learning_unit_year__acronym='FAC2')
        cls.element_luy3 = ElementLearningUnitYearFactory(learning_unit_year__academic_year=cls.academic_year,
                                                          learning_unit_year__acronym='fac3')

        GroupElementYearFactory(parent_element=cls.training_root_element, child_element=cls.common_core_element)
        GroupElementYearFactory(parent_element=cls.common_core_element, child_element=cls.subgroup_element)
        GroupElementYearFactory(parent_element=cls.training_root_element, child_element=cls.deepening_element)
        GroupElementYearChildLeafFactory(parent_element=cls.subgroup_element, child_element=cls.element_luy1)
        GroupElementYearChildLeafFactory(parent_element=cls.common_core_element, child_element=cls.element_luy2)
        GroupElementYearChildLeafFactory(parent_element=cls.deepening_element,
                                         child_element=cls.deepening_subgroup_element)
        GroupElementYearChildLeafFactory(parent_element=cls.deepening_subgroup_element, child_element=cls.element_luy3)

        cls.education_group_version = EducationGroupVersionFactory(
            offer__academic_year=cls.academic_year,
            root_group=cls.training_root_element.group_year,
            version_name=STANDARD,
        )

        cls.central_manager = CentralManagerFactory()
        cls.url = reverse(
            "learning_unit_utilization",
            kwargs={
                'root_element_id': cls.training_root_element.pk,
                'child_element_id': cls.element_luy1.pk,
            }
        )

        """
           training_root_element_particular_version
           |-- common_core_element_particular_version core
             |--- element_luy1_particular_version

       """
        cls.training_root_element_particular_version = ElementGroupYearFactory(
            group_year__education_group_type__name=TrainingType.BACHELOR.name,
            group_year__academic_year=cls.academic_year,

        )
        cls.common_core_element_particular_version = ElementGroupYearFactory(
            group_year__academic_year=cls.academic_year,
            group_year__education_group_type__name=GroupType.COMMON_CORE.name,
        )

        cls.element_luy1_particular_version = ElementLearningUnitYearFactory(learning_unit_year__academic_year=cls.academic_year)

        GroupElementYearFactory(parent_element=cls.training_root_element_particular_version,
                                child_element=cls.common_core_element_particular_version)
        GroupElementYearChildLeafFactory(parent_element=cls.common_core_element_particular_version, child_element=cls.element_luy1_particular_version)

        cls.education_group_particular_version = EducationGroupVersionFactory(
            offer__academic_year=cls.academic_year,
            root_group=cls.training_root_element_particular_version.group_year,
            version_name='CEMS',
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

    def test_assert_key_context_dict(self):

        node_identity = NodeIdentity(
            code=self.element_luy3.learning_unit_year.acronym,
            year=self.element_luy3.learning_unit_year.academic_year.year
        )
        utilization_rows = get_utilization_rows(node_identity)

        self.assertEqual(len(utilization_rows), 1)

        utilization_row = utilization_rows[0]
        self.assertIn('link', utilization_row)
        self.assertIn('training_nodes', utilization_row)

        training_nodes = utilization_rows[0]['training_nodes']
        self.assertIn('direct_gathering', training_nodes[0])
        self.assertIn('root_nodes', training_nodes[0])
        self.assertIn('version_name', training_nodes[0])

        direct_gathering = training_nodes[0]['direct_gathering']
        self.assertIn('parent', direct_gathering)
        self.assertIn('url', direct_gathering)

    def test_assert_key_context_dict_with_gathering(self):
        node_identity = NodeIdentity(
            code=self.element_luy3.learning_unit_year.acronym,
            year=self.element_luy3.learning_unit_year.academic_year.year
        )
        utilization_rows = get_utilization_rows(node_identity)
        root_nodes = utilization_rows[0]['training_nodes'][0]['root_nodes']

        root = root_nodes[0]['root']
        self.assertEqual(root.title, self.training_root_element.group_year.acronym)

        direct_gathering = utilization_rows[0]['training_nodes'][0]['direct_gathering']
        self.assertEqual(direct_gathering['parent'].title,
                         self.deepening_element.group_year.acronym)

        self.assertEqual(direct_gathering['url'],
                         reverse(URL_ELEMENT_IDENTIFICATION,
                                 kwargs={
                                     'code': self.deepening_element.group_year.partial_acronym,
                                     'year': self.deepening_element.group_year.academic_year.year}
                                 )
                         )
        self.assertEqual(utilization_rows[0]['training_nodes'][0]['version_name'], '')

        self.assertEqual(root_nodes[0]['url'],
                         reverse(URL_ELEMENT_IDENTIFICATION,
                                 kwargs={
                                     'code': self.training_root_element.group_year.partial_acronym,
                                     'year': self.training_root_element.group_year.academic_year.year
                                 }
                                 )
                         )

    def test_training_nodes_order_by_parent_title(self):
        aaa = NodeGroupYearFactory(title='AAA')
        bbb = NodeGroupYearFactory(title='BBB')
        ccc = NodeGroupYearFactory(title='CCC')

        node_group_years = [aaa, bbb, ccc]

        for x in range(5):
            ordered_list = _get_training_nodes(_build_random_list_for_training_nodes(node_group_years))
            self.assertEqual(ordered_list[0]['direct_gathering']['parent'], aaa)
            self.assertEqual(ordered_list[1]['direct_gathering']['parent'], bbb)
            self.assertEqual(ordered_list[2]['direct_gathering']['parent'], ccc)

    def test_root_nodes_order_by_link_parent_title(self):
        node_aaa = NodeGroupYearFactory(title='AAA')

        root_aaa = NodeGroupYearFactory(title='AAA_root')
        root_bbb = NodeGroupYearFactory(title='BBB_root')
        root_ccc = NodeGroupYearFactory(title='CCC_root')

        node_group_years = [root_aaa, root_bbb, root_ccc]

        for x in range(5):
            ordered_list = _get_training_nodes(_build_random_list_for_root_nodes(node_aaa, node_group_years))
            self.assertEqual(ordered_list[0]['root_nodes'][0]['root'].title, root_aaa.title)

    def test_not_in_a_training(self):
        """
        root_element
        |-- element_luy1
        """
        root_element = ElementGroupYearFactory(
            group_year__education_group_type__name=GroupType.COMMON_CORE.name,
            group_year__academic_year=self.academic_year,
        )
        luy1 = ElementLearningUnitYearFactory(learning_unit_year__academic_year=self.academic_year)

        GroupElementYearChildLeafFactory(parent_element=root_element, child_element=luy1)
        node_identity = NodeIdentity(
            code=luy1.learning_unit_year.acronym,
            year=luy1.learning_unit_year.academic_year.year
        )
        utilization_rows = get_utilization_rows(node_identity)
        training_nodes = utilization_rows[0]['training_nodes']
        self.assertCountEqual(training_nodes, [])

    def test_assert_version_name(self):
        node_identity = NodeIdentity(
            code=self.element_luy1_particular_version.learning_unit_year.acronym,
            year=self.element_luy1_particular_version.learning_unit_year.academic_year.year
        )
        utilization_rows = get_utilization_rows(node_identity)
        self.assertEqual(utilization_rows[0]['training_nodes'][0]['version_name'],
                         "[{}]".format(self.education_group_particular_version.version_name))


def _build_random_list_for_training_nodes(original: List) -> Dict:
    node_group_years = sample(original, len(original))
    node_group_years_dict = {}

    for i in node_group_years:
        node_group_years_dict.update({i: []})
    return node_group_years_dict


def _build_random_list_for_root_nodes(key, original: List) -> Dict:
    node_group_years = sample(original, len(original))
    return {key: node_group_years}
