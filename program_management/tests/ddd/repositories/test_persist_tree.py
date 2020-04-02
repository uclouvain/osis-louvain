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
from django.test import TestCase

from base.models.group_element_year import GroupElementYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import TrainingFactory, GroupFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from program_management.ddd.domain.node import NodeEducationGroupYear, NodeLearningUnitYear
from program_management.ddd.repositories import persist_tree
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestSaveTree(TestCase):
    def setUp(self):
        academic_year = AcademicYearFactory(current=True)
        training = TrainingFactory(academic_year=academic_year)
        common_core = GroupFactory(academic_year=academic_year)
        learning_unit_year = LearningUnitYearFactory(academic_year=academic_year)

        self.root_node = NodeEducationGroupYear(
            node_id=training.pk,
            acronym=training.acronym,
            title=training.title,
            year=training.academic_year.year
        )
        self.common_core_node = NodeEducationGroupYear(
            node_id=common_core.pk,
            acronym=common_core.acronym,
            title=common_core.title,
            year=common_core.academic_year.year
        )
        self.learning_unit_year_node = NodeLearningUnitYear(
            node_id=learning_unit_year.pk,
            acronym=learning_unit_year.acronym,
            title=learning_unit_year.specific_title,
            year=learning_unit_year.academic_year.year
        )

    def test_case_tree_persist_from_scratch(self):
        self.common_core_node.add_child(self.learning_unit_year_node)
        self.root_node.add_child(self.common_core_node)
        tree = ProgramTreeFactory(root_node=self.root_node)

        persist_tree.persist(tree)

        self.assertEquals(GroupElementYear.objects.all().count(), 2)

    def test_case_tree_persist_with_some_existing_part(self):
        self.root_node.add_child(self.common_core_node)
        tree = ProgramTreeFactory(root_node=self.root_node)

        persist_tree.persist(tree)
        self.assertEquals(GroupElementYear.objects.all().count(), 1)

        # Append UE to common core
        self.common_core_node.add_child(self.learning_unit_year_node)
        persist_tree.persist(tree)
        self.assertEquals(GroupElementYear.objects.all().count(), 2)

    def test_case_tree_persist_after_detach_element(self):
        self.root_node.add_child(self.common_core_node)
        tree = ProgramTreeFactory(root_node=self.root_node)

        persist_tree.persist(tree)
        self.assertEquals(GroupElementYear.objects.all().count(), 1)

        path_to_detach = "|".join([str(self.root_node.pk), str(self.common_core_node.pk)])
        tree.detach_node(path_to_detach)
        persist_tree.persist(tree)
        self.assertEquals(GroupElementYear.objects.all().count(), 0)
