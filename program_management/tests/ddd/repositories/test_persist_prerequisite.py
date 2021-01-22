# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
import copy
from unittest import mock

from django.test import TestCase

from base.models.enums import prerequisite_operator
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import TrainingType
from base.models.prerequisite import Prerequisite
from base.models.prerequisite_item import PrerequisiteItem
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.prerequisite import PrerequisiteFactory
from program_management.ddd.domain import prerequisite
from program_management.ddd.domain.prerequisite import NullPrerequisite, NullPrerequisites
from program_management.ddd.domain.program_tree import ProgramTreeIdentity
from program_management.ddd.repositories import _persist_prerequisite
from program_management.ddd.repositories.program_tree import ProgramTreeRepository
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeLearningUnitYearFactory, \
    NodeGroupYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory, ElementLearningUnitYearFactory


class TestPersist(TestCase):
    @mock.patch("program_management.ddd.repositories._persist_prerequisite._persist")
    def test_call_persist_prerequisite_on_changed_node(self, mock_persist_prerequisite):
        year = 2020
        tree = ProgramTreeFactory(root_node__year=year, root_node__node_type=TrainingType.BACHELOR)
        link1 = LinkFactory(parent=tree.root_node, child=NodeLearningUnitYearFactory(code='LDROI1001', year=year))
        link2 = LinkFactory(parent=tree.root_node, child=NodeLearningUnitYearFactory(code='LDROI1002', year=year))

        tree.set_prerequisite("LDROI1002", link1.child)

        _persist_prerequisite.persist(tree)

        mock_persist_prerequisite.assert_called_once_with(tree.root_node, tree.get_all_prerequisites()[0])


class TestPersistPrerequisite(TestCase):
    def setUp(self):
        self.current_academic_year = AcademicYearFactory(current=True)
        self.root_element = ElementGroupYearFactory(
            group_year__academic_year__current=True,
            group_year__education_group_type__category=Categories.TRAINING.name,
            group_year__education_group_type__name=TrainingType.BACHELOR.name,
        )
        self.education_group_version = EducationGroupVersionFactory(
            root_group=self.root_element.group_year,
            offer__academic_year__current=True
        )
        self.program_tree_identity = ProgramTreeIdentity(
            code=self.root_element.group_year.partial_acronym,
            year=self.root_element.group_year.academic_year.year
        )

        self.element_learning_unit_year = ElementLearningUnitYearFactory(
            learning_unit_year__academic_year__current=True,
            learning_unit_year__acronym="LDROI1001"
        )
        GroupElementYearFactory(parent_element=self.root_element, child_element=self.element_learning_unit_year)

        element1 = ElementLearningUnitYearFactory(
            learning_unit_year__acronym="LOSIS4525",
            learning_unit_year__academic_year__current=True
        )
        self.luy1 = element1.learning_unit_year
        element2 = ElementLearningUnitYearFactory(
            learning_unit_year__acronym="MARC4123",
            learning_unit_year__academic_year__current=True
        )
        self.luy2 = element2.learning_unit_year
        GroupElementYearFactory(parent_element=self.root_element, child_element=element1)
        GroupElementYearFactory(parent_element=self.root_element, child_element=element2)

    def test_when_null_prerequisite_given(self):
        tree = ProgramTreeRepository().get(self.program_tree_identity)
        node_having_prerequisites = tree.get_node_by_code_and_year("LDROI1001", self.current_academic_year.year)
        tree.set_prerequisite("", node_having_prerequisites)
        _persist_prerequisite.persist(tree)

        self.assertQuerysetEqual(
            Prerequisite.objects.filter(
                education_group_version__root_group__element__pk=tree.root_node.node_id
            ),
            []
        )

    def test_should_create_prerequisite(self):
        tree = ProgramTreeRepository().get(self.program_tree_identity)
        node_having_prerequisites = tree.get_node_by_code_and_year("LDROI1001", self.current_academic_year.year)
        tree.set_prerequisite("LOSIS4525 OU MARC4123", node_having_prerequisites)

        _persist_prerequisite.persist(tree)

        prerequisite_obj = Prerequisite.objects.get(
            education_group_version__root_group__element__pk=tree.root_node.node_id
        )
        self.assertTrue(
            PrerequisiteItem.objects.filter(prerequisite=prerequisite_obj)
        )

    def test_should_update_main_operator(self):
        tree = ProgramTreeRepository().get(self.program_tree_identity)
        node_having_prerequisites = tree.get_node_by_code_and_year("LDROI1001", self.current_academic_year.year)
        tree.set_prerequisite("LOSIS4525 OU MARC4123", node_having_prerequisites)

        _persist_prerequisite.persist(tree)

        tree.set_prerequisite("LOSIS4525 ET MARC4123", node_having_prerequisites)
        _persist_prerequisite.persist(tree)

        prerequisite_obj = Prerequisite.objects.get(
            education_group_version__root_group__element__pk=tree.root_node.node_id,
            main_operator=prerequisite_operator.AND
        )
        self.assertTrue(prerequisite_obj)

    def test_should_empty_existing_prerequisites(self):
        PrerequisiteFactory(
            education_group_version=self.education_group_version,
            learning_unit_year=self.element_learning_unit_year.learning_unit_year,
            items__groups=((self.luy1,), (self.luy2,))
        )
        tree = ProgramTreeRepository().get(self.program_tree_identity)
        node_having_prerequisites = tree.get_node_by_code_and_year("LDROI1001", self.current_academic_year.year)
        tree.set_prerequisite("", node_having_prerequisites)

        _persist_prerequisite.persist(tree)

        self.assertQuerysetEqual(
            Prerequisite.objects.filter(
                education_group_version__root_group__element__pk=tree.root_node.node_id
            ),
            []
        )
