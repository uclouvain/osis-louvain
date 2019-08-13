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

from django.templatetags.static import static
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.business.education_groups.group_element_year_tree import EducationGroupHierarchy
from base.models.enums.education_group_types import MiniTrainingType, GroupType
from base.models.enums.link_type import LinkTypes
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.prerequisite import PrerequisiteFactory
from base.tests.factories.prerequisite_item import PrerequisiteItemFactory


class TestBuildTree(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory()
        self.parent = EducationGroupYearFactory(academic_year=self.academic_year)
        self.group_element_year_1 = GroupElementYearFactory(
            parent=self.parent,
            child_branch=EducationGroupYearFactory(academic_year=self.academic_year)
        )
        self.group_element_year_1_1 = GroupElementYearFactory(
            parent=self.group_element_year_1.child_branch,
            child_branch=EducationGroupYearFactory(academic_year=self.academic_year)
        )
        self.group_element_year_2 = GroupElementYearFactory(
            parent=self.parent,
            child_branch=EducationGroupYearFactory(academic_year=self.academic_year)
        )
        self.learning_unit_year_1 = LearningUnitYearFactory()
        self.group_element_year_2_1 = GroupElementYearFactory(
            parent=self.group_element_year_2.child_branch,
            child_branch=None,
            child_leaf=self.learning_unit_year_1
        )

    def test_init_tree(self):
        node = EducationGroupHierarchy(self.parent)

        self.assertEqual(node.education_group_year, self.parent)
        self.assertEqual(len(node.children), 2)
        self.assertEqual(node.children[0].group_element_year, self.group_element_year_1)
        self.assertEqual(node.children[1].group_element_year, self.group_element_year_2)

        self.assertEqual(node.children[0].children[0].group_element_year, self.group_element_year_1_1)
        self.assertEqual(node.children[1].children[0].group_element_year, self.group_element_year_2_1)

        self.assertEqual(node.children[0].children[0].education_group_year, self.group_element_year_1_1.child_branch)
        self.assertEqual(node.children[1].children[0].education_group_year, None)
        self.assertEqual(node.children[1].children[0].learning_unit_year, self.group_element_year_2_1.child_leaf)

    def test_tree_to_json(self):
        node = EducationGroupHierarchy(self.parent)

        json = node.to_json()
        self.assertEqual(json['text'], self.parent.verbose)

        self.assertEqual(json['a_attr']['href'], reverse('education_group_read', args=[
            self.parent.pk, self.parent.pk]) + "?group_to_parent=0")

        self.assertEqual(
            json['children'][1]['children'][0]['a_attr']['href'],
            reverse(
                'learning_unit_utilization',
                args=[self.parent.pk, self.group_element_year_2_1.child_leaf.pk]
            ) + "?group_to_parent={}".format(self.group_element_year_2_1.pk)
        )

    def test_tree_get_url(self):
        test_cases = [
            {'name': 'with tab',
             'node': EducationGroupHierarchy(self.parent, tab_to_show='show_identification'),
             'correct_url': reverse('education_group_read', args=[self.parent.pk, self.parent.pk]) +
             "?group_to_parent=0&tab_to_show=show_identification"},
            {'name': 'without tab',
             'node': EducationGroupHierarchy(self.parent),
             'correct_url': reverse('education_group_read',
                                    args=[self.parent.pk, self.parent.pk]) + "?group_to_parent=0"},
            {'name': 'with wrong tab',
             'node': EducationGroupHierarchy(self.parent, tab_to_show='not_existing'),
             'correct_url': reverse('education_group_read',
                                    args=[self.parent.pk, self.parent.pk]) + "?group_to_parent=0"},
        ]

        for case in test_cases:
            with self.subTest(type=case['name']):
                self.assertEqual(case['correct_url'], case['node'].get_url())

    def test_tree_luy_has_prerequisite(self):
        # self.learning_unit_year_1 has prerequisite
        PrerequisiteItemFactory(
            prerequisite=PrerequisiteFactory(
                learning_unit_year=self.learning_unit_year_1,
                education_group_year=self.parent
            )
        )

        node = EducationGroupHierarchy(self.parent)
        json = node.to_json()

        self.assertEqual(
            json['children'][1]['children'][0]['a_attr']['title'],
            "{}\n{}".format(self.learning_unit_year_1.complete_title, _("The learning unit has prerequisites"))
        )
        self.assertEqual(
            json['children'][1]['children'][0]['icon'],
            'fa fa-arrow-left'
        )

    def test_tree_luy_is_prerequisite(self):
        # self.learning_unit_year_1 is prerequisite
        PrerequisiteItemFactory(
            learning_unit=self.learning_unit_year_1.learning_unit,
            prerequisite=PrerequisiteFactory(education_group_year=self.parent)
        )

        node = EducationGroupHierarchy(self.parent)
        json = node.to_json()

        self.assertEqual(
            json['children'][1]['children'][0]['a_attr']['title'],
            "{}\n{}".format(self.learning_unit_year_1.complete_title, _("The learning unit is a prerequisite"))
        )
        self.assertEqual(
            json['children'][1]['children'][0]['icon'],
            'fa fa-arrow-right'
        )

    def test_tree_luy_has_and_is_prerequisite(self):
        # self.learning_unit_year_1 is prerequisite
        PrerequisiteItemFactory(
            learning_unit=self.learning_unit_year_1.learning_unit,
            prerequisite=PrerequisiteFactory(education_group_year=self.parent)
        )
        # self.learning_unit_year_1 has prerequisite
        PrerequisiteItemFactory(
            prerequisite=PrerequisiteFactory(
                learning_unit_year=self.learning_unit_year_1,
                education_group_year=self.parent
            )
        )

        node = EducationGroupHierarchy(self.parent)
        json = node.to_json()

        self.assertEqual(
            json['children'][1]['children'][0]['a_attr']['title'],
            "{}\n{}".format(
                self.learning_unit_year_1.complete_title,
                _("The learning unit has prerequisites and is a prerequisite")
            )
        )
        self.assertEqual(
            json['children'][1]['children'][0]['icon'],
            'fa fa-exchange-alt'
        )

    def test_tree_to_json_a_attr(self):
        """In this test, we ensure that a attr contains some url for tree contextual menu"""
        node = EducationGroupHierarchy(self.parent)
        json = node.to_json()
        child = self.group_element_year_1.child_branch

        expected_modify_url = reverse('group_element_year_update', args=[
            self.parent.pk, child.pk, self.group_element_year_1.pk
        ])
        self.assertEqual(json['children'][0]['a_attr']['modify_url'], expected_modify_url)

        expected_attach_url = reverse('education_group_attach', args=[self.parent.pk, child.pk])
        self.assertEqual(json['children'][0]['a_attr']['attach_url'], expected_attach_url)

        expected_detach_url = reverse('group_element_year_delete', args=[
            self.parent.pk, child.pk, self.group_element_year_1.pk
        ])
        self.assertEqual(json['children'][0]['a_attr']['detach_url'], expected_detach_url)

    def test_build_tree_reference(self):
        """
        This tree contains a reference link.
        """
        self.group_element_year_1.link_type = LinkTypes.REFERENCE.name
        self.group_element_year_1.save()

        node = EducationGroupHierarchy(self.parent)

        self.assertEqual(node.children[0]._get_icon(), static('img/reference.jpg'))

        list_children = node.to_list()
        self.assertEqual(list_children, [
            self.group_element_year_1_1,
            self.group_element_year_2, [self.group_element_year_2_1]
        ])

    def test_node_to_list_flat(self):
        node = EducationGroupHierarchy(self.parent)
        list_children = node.to_list(flat=True)

        self.assertCountEqual(list_children, [
            self.group_element_year_1,
            self.group_element_year_1_1,
            self.group_element_year_2,
            self.group_element_year_2_1
        ])

    def test_node_to_list_with_pruning_function(self):
        """
        This test ensure that if the parameter pruning function is specified we only get the tree
        without node which has been pruned
        """
        node = EducationGroupHierarchy(self.parent)
        list_children = node.to_list(
            flat=True,
            pruning_function=lambda child: child.group_element_year.pk == self.group_element_year_2.pk
        )

        self.assertCountEqual(list_children, [self.group_element_year_2])


class TestGetOptionList(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory(current=True)
        self.root = EducationGroupYearFactory(academic_year=self.academic_year)

    def test_get_option_list_case_no_result(self):
        node = EducationGroupHierarchy(self.root)
        self.assertListEqual(node.get_option_list(), [])

    def test_get_option_list_case_result_found(self):
        option_1 = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__name=MiniTrainingType.OPTION.name
        )
        GroupElementYearFactory(parent=self.root, child_branch=option_1)
        node = EducationGroupHierarchy(self.root)

        self.assertListEqual(node.get_option_list(), [option_1])

    def test_get_option_list_case_reference_link(self):
        """
          This test ensure that the tree will not be pruned when the link of child is reference
        """
        reference_group_child = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__name=GroupType.SUB_GROUP.name
        )
        GroupElementYearFactory(
            parent=self.root,
            child_branch=reference_group_child,
            link_type=LinkTypes.REFERENCE.name,
        )

        option_1 = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__name=MiniTrainingType.OPTION.name
        )
        GroupElementYearFactory(parent=reference_group_child, child_branch=option_1)
        node = EducationGroupHierarchy(self.root)

        self.assertListEqual(node.get_option_list(), [option_1])

    def test_get_option_list_case_multiple_result_found_on_different_children(self):
        list_option = []
        for _ in range(5):
            group_child = EducationGroupYearFactory(
                academic_year=self.academic_year,
                education_group_type__name=GroupType.SUB_GROUP.name
            )
            GroupElementYearFactory(parent=self.root, child_branch=group_child)

            option = EducationGroupYearFactory(
                academic_year=self.academic_year,
                education_group_type__name=MiniTrainingType.OPTION.name
            )
            list_option.append(option)
            GroupElementYearFactory(parent=group_child, child_branch=option)

        node = EducationGroupHierarchy(self.root)
        self.assertCountEqual(node.get_option_list(), list_option)

    def test_get_option_list_case_ignore_finality_list_choice(self):
        """
        This test ensure that the tree will be pruned when a child if type of finality list choice and option
        isn't considered as part of tree
        """
        option_1 = EducationGroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__name=MiniTrainingType.OPTION.name
        )
        GroupElementYearFactory(parent=self.root, child_branch=option_1)

        for finality_type in [GroupType.FINALITY_120_LIST_CHOICE.name, GroupType.FINALITY_180_LIST_CHOICE.name]:
            finality_group = EducationGroupYearFactory(
                academic_year=self.academic_year,
                education_group_type__name=finality_type
            )
            GroupElementYearFactory(parent=self.root, child_branch=finality_group)
            GroupElementYearFactory(parent=finality_group, child_branch=EducationGroupYearFactory(
                academic_year=self.academic_year,
                education_group_type__name=MiniTrainingType.OPTION.name
            ))

        node = EducationGroupHierarchy(self.root)
        self.assertListEqual(node.get_option_list(), [option_1])
