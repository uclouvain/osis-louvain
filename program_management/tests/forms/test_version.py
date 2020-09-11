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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import mock
from django.test import TestCase

from base.models.enums.education_group_types import TrainingType, MiniTrainingType
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from program_management.ddd.domain.node import NodeIdentity
from program_management.forms.version import UpdateTrainingVersionForm, UpdateMiniTrainingVersionForm
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionIdentityFactory


class TestTrainingVersionForm(TestCase):

    def setUp(self) -> None:
        self.tree_version_identity = ProgramTreeVersionIdentityFactory()
        self.node_identity = NodeIdentity(code='CODE', year=self.tree_version_identity.year)
        self.user = PersonFactory().user

    @mock.patch('program_management.forms.version.SpecificVersionForm._init_academic_year_choices')
    def test_field_reference_should_use_group_form(self, *mocks):
        form = UpdateTrainingVersionForm(
            self.tree_version_identity,
            self.node_identity,
            TrainingType.PGRM_MASTER_120,
            self.user
        )
        self.assertEqual(form.field_reference("field"), 'GroupForm.PGRM_MASTER_120.field')
        assertion_message = "The training version form fields updatable are only fields from Group."
        self.assertNotEqual(form.field_reference("field"), 'TrainingForm.PGRM_MASTER_120.field', assertion_message)


class TestMiniTrainingVersionForm(TestCase):

    def setUp(self) -> None:
        self.tree_version_identity = ProgramTreeVersionIdentityFactory()
        self.node_identity = NodeIdentity(code='CODE', year=self.tree_version_identity.year)
        self.user = PersonFactory().user

    @mock.patch('program_management.forms.version.SpecificVersionForm._init_academic_year_choices')
    def test_field_reference_should_use_group_form(self, *mocks):
        form = UpdateMiniTrainingVersionForm(
            self.tree_version_identity,
            self.node_identity,
            MiniTrainingType.DEEPENING,
            self.user
        )
        self.assertEqual(form.field_reference("field"), 'GroupForm.DEEPENING.field')
        assertion_message = "The mini-training version form fields updatable are only fields from Group."
        self.assertNotEqual(form.field_reference("field"), 'MiniTrainingForm.DEEPENING.field', assertion_message)
