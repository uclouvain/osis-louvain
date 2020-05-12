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
from unittest import mock

from django.test import TestCase

from base.models.enums import prerequisite_operator
from base.models.prerequisite import Prerequisite
from base.models.prerequisite_item import PrerequisiteItem
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.prerequisite import PrerequisiteFactory
from program_management.ddd.domain import prerequisite
from program_management.ddd.domain.prerequisite import NullPrerequisite
from program_management.ddd.repositories import _persist_prerequisite
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeEducationGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory


class TestPersist(TestCase):
    @mock.patch("program_management.ddd.repositories._persist_prerequisite._persist")
    def test_call_persist_prerequisite_on_changed_node(self, mock_persist_prerequisite):
        tree = ProgramTreeFactory()
        link1 = LinkFactory(parent=tree.root_node, child=NodeLearningUnitYearFactory())
        link2 = LinkFactory(parent=tree.root_node, child=NodeLearningUnitYearFactory())

        link1.child.set_prerequisite(NullPrerequisite())

        _persist_prerequisite.persist(tree)

        mock_persist_prerequisite.assert_called_once_with(tree.root_node, link1.child)


class TestPersistPrerequisite(TestCase):
    def setUp(self):
        self.current_academic_year = AcademicYearFactory(current=True)
        self.root_education_group_year = EducationGroupYearFactory(academic_year__current=True)
        self.root_node = NodeEducationGroupYearFactory(node_id=self.root_education_group_year.pk)

        self.learning_unit_year = LearningUnitYearFactory(academic_year__current=True)
        self.node = NodeLearningUnitYearFactory(node_id=self.learning_unit_year.pk)

        self.luy1 = LearningUnitYearFactory(acronym="LOSIS4525", academic_year__current=True)
        self.luy2 = LearningUnitYearFactory(acronym="MARC4123", academic_year__current=True)

    def test_when_null_prerequisite_given(self):
        self.node.prerequisite = NullPrerequisite()
        _persist_prerequisite._persist(self.root_node, self.node)

        prerequisite_obj = Prerequisite.objects.get(education_group_year__id=self.root_node.node_id)
        self.assertFalse(
            PrerequisiteItem.objects.filter(prerequisite=prerequisite_obj)
        )

    def test_should_create_prerequisite(self):
        prerequisite_obj = prerequisite.factory.from_expression(
            "LOSIS4525 OU MARC4123",
            self.current_academic_year.year
        )
        self.node.prerequisite = prerequisite_obj
        _persist_prerequisite._persist(self.root_node, self.node)

        prerequisite_obj = Prerequisite.objects.get(education_group_year__id=self.root_node.node_id)
        self.assertTrue(
            PrerequisiteItem.objects.filter(prerequisite=prerequisite_obj)
        )

    def test_should_update_main_operator(self):
        prerequisite_obj = prerequisite.factory.from_expression(
            "LOSIS4525 OU MARC4123",
            self.current_academic_year.year
        )
        self.node.prerequisite = prerequisite_obj
        _persist_prerequisite._persist(self.root_node, self.node)

        prerequisite_obj = prerequisite.factory.from_expression(
            "LOSIS4525 ET MARC4123",
            self.current_academic_year.year
        )
        self.node.prerequisite = prerequisite_obj
        _persist_prerequisite._persist(self.root_node, self.node)

        prerequisite_obj = Prerequisite.objects.get(
            education_group_year__id=self.root_node.node_id,
            main_operator=prerequisite_operator.AND
        )
        self.assertTrue(prerequisite_obj)

    def test_should_empty_existing_prerequisites(self):
        PrerequisiteFactory(
            education_group_year=self.root_education_group_year,
            learning_unit_year=self.learning_unit_year,
            items__groups=((self.luy1,), (self.luy2,))
        )
        self.node.prerequisite = NullPrerequisite()
        _persist_prerequisite._persist(self.root_node, self.node)

        prerequisite_obj = Prerequisite.objects.get(education_group_year__id=self.root_node.node_id)
        self.assertFalse(
            PrerequisiteItem.objects.filter(prerequisite=prerequisite_obj)
        )

