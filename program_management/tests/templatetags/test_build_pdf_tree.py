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
from django.template import Context, Template
from django.test import TestCase

from base.models.enums.learning_component_year_type import LECTURING, PRACTICAL_EXERCISES
from base.models.enums.learning_unit_year_periodicity import BIENNIAL_ODD, BIENNIAL_EVEN
from base.templatetags.education_group_pdf import pdf_tree_list
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from program_management.ddd.repositories import load_tree
from program_management.tests.factories.element import ElementGroupYearFactory, ElementLearningUnitYearFactory


def _build_correct_tree_list(tree):
    return pdf_tree_list(tree)


class TestBuildPDFTree(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory()
        self.education_group_year_1 = ElementGroupYearFactory(
            group_year__credits=10,
            group_year__academic_year=self.academic_year
        )
        self.education_group_year_2 = ElementGroupYearFactory(
            group_year__credits=20,
            group_year__academic_year=self.academic_year
        )
        self.element_learning_unit_year_1 = ElementLearningUnitYearFactory()
        self.element_learning_unit_year_2 = ElementLearningUnitYearFactory(learning_unit_year__periodicity=BIENNIAL_ODD)
        self.element_learning_unit_year_3 = ElementLearningUnitYearFactory(learning_unit_year__status=False)
        self.element_learning_unit_year_4 = ElementLearningUnitYearFactory(
            learning_unit_year__periodicity=BIENNIAL_EVEN
        )

        self.group_element_year_1 = GroupElementYearFactory(
            parent_element=self.education_group_year_1,
            child_element=self.education_group_year_2,
            is_mandatory=True
        )
        self.group_element_year_2 = GroupElementYearChildLeafFactory(
            parent_element=self.education_group_year_2,
            child_element=self.element_learning_unit_year_1,
            is_mandatory=True
        )
        self.group_element_year_3 = GroupElementYearChildLeafFactory(
            parent_element=self.education_group_year_2,
            child_element=self.element_learning_unit_year_2,
            is_mandatory=True,
        )
        self.group_element_year_4 = GroupElementYearChildLeafFactory(
            parent_element=self.education_group_year_2,
            child_element=self.element_learning_unit_year_3,
            is_mandatory=True
        )

        for elem_learning_unit_year in [ self.element_learning_unit_year_1, self.element_learning_unit_year_2,
                                         self.element_learning_unit_year_3, self.element_learning_unit_year_4]:
            LearningComponentYearFactory(
                learning_unit_year=elem_learning_unit_year.learning_unit_year,
                type=LECTURING
            )
            LearningComponentYearFactory(
                learning_unit_year=elem_learning_unit_year.learning_unit_year,
                type=PRACTICAL_EXERCISES
            )

    def test_build_pdf_tree_with_mandatory(self):
        tree = load_tree.load(self.education_group_year_1.id)
        out = Template(
            "{% load education_group_pdf %}"
            "{{ tree|pdf_tree_list }}"
        ).render(Context({
            'tree': tree.root_node.children
        }))
        self.assertEqual(out, _build_correct_tree_list(tree.root_node.children))

    def test_build_pdf_tree_with_optional(self):
        self.group_element_year_1.is_mandatory = False
        self.group_element_year_1.save()
        self.group_element_year_2.is_mandatory = False
        self.group_element_year_2.save()

        tree = load_tree.load(self.education_group_year_1.id)
        out = Template(
            "{% load education_group_pdf %}"
            "{{ tree|pdf_tree_list }}"
        ).render(Context({
            'tree': tree.root_node.children
        }))
        self.assertEqual(out, _build_correct_tree_list(tree.root_node.children))

    def test_tree_list_with_none(self):
        out = Template(
            "{% load education_group_pdf %}"
            "{{ tree|pdf_tree_list }}"
        ).render(Context({
            'tree': []
        }))
        self.assertEqual(out, "")

    def test_tree_list_with_empty(self):
        out = Template(
            "{% load education_group_pdf %}"
            "{{ tree|pdf_tree_list }}"
        ).render(Context({
            'tree': []
        }))
        self.assertEqual(out, "")
