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
from django.http import HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse

from base.models.enums.education_group_types import GroupType, TrainingType, MiniTrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from base.tests.factories.person import PersonFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from program_management.ddd.domain.program_tree_version import STANDARD
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory, ElementLearningUnitYearFactory


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
        cls.element_luy1 = ElementLearningUnitYearFactory(learning_unit_year__academic_year=cls.academic_year,
                                                          learning_unit_year__acronym='fac1')
        cls.element_luy2 = ElementLearningUnitYearFactory(learning_unit_year__academic_year=cls.academic_year,
                                                          learning_unit_year__acronym='fac2')
        cls.element_luy3 = ElementLearningUnitYearFactory(learning_unit_year__academic_year=cls.academic_year,
                                                          learning_unit_year__acronym='fac3')

        GroupElementYearFactory(parent_element=cls.training_root_element, child_element=cls.common_core_element)
        GroupElementYearFactory(parent_element=cls.common_core_element, child_element=cls.subgroup_element)
        GroupElementYearFactory(parent_element=cls.training_root_element, child_element=cls.deepening_element)
        GroupElementYearChildLeafFactory(parent_element=cls.subgroup_element, child_element=cls.element_luy1)
        GroupElementYearChildLeafFactory(parent_element=cls.common_core_element, child_element=cls.element_luy2)
        GroupElementYearChildLeafFactory(parent_element=cls.deepening_element, child_element=cls.element_luy3)
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
        response = self.client.get(self.url)
        utilization_rows = response.context['utilization_rows']
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

        root_nodes = training_nodes[0]['root_nodes']
        self.assertCountEqual(root_nodes, [])

    def test_assert_key_context_dict_with_gathering(self):
        # print('ici') rouve pas d'arbre??????pq
        url_gathering = reverse(
            "learning_unit_utilization",
            kwargs={
                'root_element_id': self.training_root_element.pk,
                'child_element_id': self.element_luy3.pk,
            }
        )
        response = self.client.get(url_gathering)
        root_nodes = response.context['utilization_rows'][0]['training_nodes'][0]['root_nodes']
        print(root_nodes)
        self.assertIn('root', root_nodes[0])
        self.assertIn('version_name', root_nodes[0])
        self.assertIn('url', root_nodes[0])

    def test_context_utilization_rows_content(self):
        response = self.client.get(self.url)
        print(len(response.context['utilization_rows']))
        print('//////////////////////////')
        link = response.context['utilization_rows'][0]['link']
        training_nodes = response.context['utilization_rows'][0]['training_nodes']
        print("link {}".format(link.parent.title))
        for r in training_nodes:

            print("direct {}".format(r['direct_gathering']['parent'].title))
            for i in r.get('root_nodes'):
                print(i['root'].title)
        print('//////////////////////////')

        self.assertEqual(link.parent.title, self.subgroup_element.group_year.acronym)
        #
        # print(response.context['utilization_rows'][0]['training_nodes'])
        # print(response.context['utilization_rows'][0]['training_nodes'])
        # """
        # training_root_element 100
        # |-- common code 101
        #   |--- subgroup_element 102
        #       |--- element_luy1
        #   |-- element_luy2
        # """


# {% for row in utilization_rows %}
#         <tr>
#         <td> {% if row.link.is_reference %}  <img src="{% static 'img/reference.jpg' %}"> {% endif %} </td>
#         <td>
#             {% url 'element_identification' row.link.parent.year row.link.parent.code as url_parent_identification %}
#             <a href="{{ url_parent_identification }}">{{ row.link.parent.code | default_if_none:'' }}</a>
#         </td>
#         <td>{{ row.link.parent.title | default_if_none:'' }}{{ row.link_parent_version_label }}</td>
#         <td>{{ row.link.parent.group_title_fr | default_if_none:'' }}</td>
#         <td>
#             {{ row.link.relative_credits | default_if_none:'-' }} /
#             {{ row.link.child.credits.normalize | default_if_none:'-' }}
#         </td>
#         <td>{{ row.link.is_mandatory | yesno:_("yes,no") | title }}</td>
#         <td>{{ row.link.block | default_if_none:'-' }}</td>
#         <td>
#             {% for root in row.training_nodes %}
#                 <ul>
#                     <li>
#                         <a href="{{ root.direct_gathering.url }}">
#                             {{ root.direct_gathering.parent.title }}{{ root.version_name }}
#                         </a>
#                         {% if root.root_nodes %}
#                             <ul><li>
#                                 {% for root_node in root.root_nodes %}
#                                     {% if forloop.first %}{% trans 'Included in' %} : {% else %} - {% endif %}
#                                     <a href="{{ root_node.url }}">{{ root_node.root.title }}{{ root_node.version_name }}</a>
#                                     {% if forloop.last %}{% endif %}
#                                 {% endfor %}</li>
#                             </ul>
#                         {% endif %}

