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

from base.business.education_groups.group_element_year_tree import EducationGroupHierarchy
from base.models.enums.learning_component_year_type import LECTURING, PRACTICAL_EXERCISES
from base.models.enums.learning_unit_year_periodicity import BIENNIAL_ODD, BIENNIAL_EVEN
from base.templatetags.education_group_pdf import pdf_tree_list
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory


def _build_correct_tree_list(tree):
    return pdf_tree_list(tree)


class TestBuildPDFTree(TestCase):
    def setUp(self):
        self.academic_year = AcademicYearFactory()
        self.education_group_year_1 = EducationGroupYearFactory(credits=10, academic_year=self.academic_year)
        self.education_group_year_2 = EducationGroupYearFactory(credits=20, academic_year=self.academic_year)
        self.learning_unit_year_1 = LearningUnitYearFactory()
        self.learning_unit_year_2 = LearningUnitYearFactory(periodicity=BIENNIAL_ODD)
        self.learning_unit_year_3 = LearningUnitYearFactory(status=False)
        self.learning_unit_year_4 = LearningUnitYearFactory(periodicity=BIENNIAL_EVEN)
        self.group_element_year_1 = GroupElementYearFactory(parent=self.education_group_year_1,
                                                            child_branch=self.education_group_year_2,
                                                            is_mandatory=True)
        self.group_element_year_2 = GroupElementYearFactory(parent=self.education_group_year_2,
                                                            child_branch=None,
                                                            child_leaf=self.learning_unit_year_1,
                                                            is_mandatory=True)
        self.group_element_year_3 = GroupElementYearFactory(parent=self.education_group_year_2,
                                                            child_branch=None,
                                                            child_leaf=self.learning_unit_year_2,
                                                            is_mandatory=True)
        self.group_element_year_4 = GroupElementYearFactory(parent=self.education_group_year_2,
                                                            child_branch=None,
                                                            child_leaf=self.learning_unit_year_3,
                                                            is_mandatory=True)
        self.learning_component_year_1 = LearningComponentYearFactory(
            learning_container_year=self.learning_unit_year_1.learning_container_year,
            type=LECTURING
        )
        self.learning_component_year_2 = LearningComponentYearFactory(
            learning_container_year=self.learning_unit_year_1.learning_container_year,
            type=PRACTICAL_EXERCISES
        )
        self.learning_component_year_3 = LearningComponentYearFactory(
            learning_container_year=self.learning_unit_year_2.learning_container_year,
            type=LECTURING
        )
        self.learning_component_year_4 = LearningComponentYearFactory(
            learning_container_year=self.learning_unit_year_2.learning_container_year,
            type=PRACTICAL_EXERCISES
        )
        self.learning_component_year_5 = LearningComponentYearFactory(
            learning_container_year=self.learning_unit_year_3.learning_container_year,
            type=LECTURING
        )
        self.learning_component_year_6 = LearningComponentYearFactory(
            learning_container_year=self.learning_unit_year_3.learning_container_year,
            type=PRACTICAL_EXERCISES
        )
        self.learning_component_year_7 = LearningComponentYearFactory(
            learning_container_year=self.learning_unit_year_4.learning_container_year,
            type=LECTURING
        )

    def test_build_pdf_tree_with_mandatory(self):
        tree = EducationGroupHierarchy(self.education_group_year_1).to_list()
        out = Template(
            "{% load education_group_pdf %}"
            "{{ tree|pdf_tree_list }}"
        ).render(Context({
            'tree': tree
        }))
        self.assertEqual(out, _build_correct_tree_list(tree))

    def test_build_pdf_tree_with_optional(self):
        self.group_element_year_1.is_mandatory = False
        self.group_element_year_1.save()
        self.group_element_year_2.is_mandatory = False
        self.group_element_year_2.save()

        tree = EducationGroupHierarchy(self.education_group_year_1).to_list()
        out = Template(
            "{% load education_group_pdf %}"
            "{{ tree|pdf_tree_list }}"
        ).render(Context({
            'tree': tree
        }))
        self.assertEqual(out, _build_correct_tree_list(tree))

    def test_tree_list_with_none(self):
        out = Template(
            "{% load education_group_pdf %}"
            "{{ tree|pdf_tree_list }}"
        ).render(Context({
            'tree': None
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
