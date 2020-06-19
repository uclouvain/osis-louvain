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

import factory.fuzzy
from django.test import SimpleTestCase

import program_management.forms
from base.models.enums.education_group_types import MiniTrainingType, GroupType
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.forms.tree.paste import PasteNodeForm
from program_management.tests.ddd.factories.authorized_relationship import AuthorizedRelationshipListFactory, \
    AuthorizedRelationshipObjectFactory
from program_management.tests.ddd.factories.node import NodeEducationGroupYearFactory, NodeLearningUnitYearFactory, \
    NodeGroupYearFactory
from program_management.ddd.repositories import node as node_repository


class TestAttachNodeFormFactory(SimpleTestCase):
    def _mock_load_node(self, return_values):
        patcher_load = mock.patch("program_management.ddd.repositories.load_node.load")
        self.addCleanup(patcher_load.stop)
        self.mock_load = patcher_load.start()
        self.mock_load.return_value = return_values

    def _mock_node_repo_get(self, return_values):
        patcher_load = mock.patch.object(node_repository.NodeRepository, "get")
        self.addCleanup(patcher_load.stop)
        self.mock_load = patcher_load.start()
        self.mock_load.return_value = return_values

    def _mock_load_authorized_relationships(self, return_value):
        patcher_load = mock.patch("program_management.ddd.repositories.load_authorized_relationship.load")
        self.addCleanup(patcher_load.stop)
        self.mock_load = patcher_load.start()
        self.mock_load.return_value = return_value

    def test_form_returned_when_child_node_is_a_learning_unit(self):
        path = "1|2"
        node_to_attach_from = NodeEducationGroupYearFactory(node_id=2)
        node_to_attach = NodeLearningUnitYearFactory()
        self._mock_load_node(node_to_attach_from)
        self._mock_node_repo_get(node_to_attach)

        relationships = AuthorizedRelationshipListFactory()
        self._mock_load_authorized_relationships(relationships)

        form = program_management.forms.tree.paste.paste_form_factory(
            None,
            path,
            node_to_attach.code,
            node_to_attach.year
        )
        self.assertIsInstance(form, program_management.forms.tree.paste.PasteLearningUnitForm)

    def test_form_returned_when_relationship_is_not_authorized(self):
        path = "9|4|5"
        node_to_attach_from = NodeEducationGroupYearFactory(node_id=5)
        node_to_attach = NodeEducationGroupYearFactory(node_type=MiniTrainingType.FSA_SPECIALITY)
        self._mock_load_node(node_to_attach_from)
        self._mock_node_repo_get(node_to_attach)

        relationships = AuthorizedRelationshipListFactory(
            authorized_relationships=[AuthorizedRelationshipObjectFactory(child_type=MiniTrainingType.SOCIETY_MINOR)]
        )
        self._mock_load_authorized_relationships(relationships)

        form = program_management.forms.tree.paste.paste_form_factory(
            None,
            path,
            node_to_attach.code,
            node_to_attach.year
        )
        self.assertIsInstance(form, program_management.forms.tree.paste.PasteNotAuthorizedChildren)

    def test_form_returned_when_parent_is_minor_major_list_choice(self):
        path = "6"
        node_to_attach_from = NodeEducationGroupYearFactory(
            node_type=factory.fuzzy.FuzzyChoice(GroupType.minor_major_list_choice_enums()),
            node_id=6
        )
        node_to_attach = NodeEducationGroupYearFactory()
        self._mock_load_node(node_to_attach_from)
        self._mock_node_repo_get(node_to_attach)

        relationship_object = AuthorizedRelationshipObjectFactory(
            parent_type=node_to_attach_from.node_type,
            child_type=node_to_attach.node_type
        )
        relationships = AuthorizedRelationshipListFactory(
            authorized_relationships=[relationship_object]
        )
        self._mock_load_authorized_relationships(relationships)

        form = program_management.forms.tree.paste.paste_form_factory(
            None,
            path,
            node_to_attach.code,
            node_to_attach.year
        )
        self.assertIsInstance(form, program_management.forms.tree.paste.PasteToMinorMajorListChoiceForm)

    def test_form_returned_when_parent_is_training_and_child_is_minor_major_list_choice(self):
        path = "65|589"
        node_to_attach_from = NodeEducationGroupYearFactory()
        node_to_attach = NodeEducationGroupYearFactory(
            node_type=factory.fuzzy.FuzzyChoice(GroupType.minor_major_list_choice_enums())
        )
        self._mock_load_node(node_to_attach_from)
        self._mock_node_repo_get(node_to_attach)

        relationship_object = AuthorizedRelationshipObjectFactory(
            parent_type=node_to_attach_from.node_type,
            child_type=node_to_attach.node_type
        )
        relationships = AuthorizedRelationshipListFactory(
            authorized_relationships=[relationship_object]
        )
        self._mock_load_authorized_relationships(relationships)

        form = program_management.forms.tree.paste.paste_form_factory(
            None,
            path,
            node_to_attach.code,
            node_to_attach.year
        )
        self.assertIsInstance(form, program_management.forms.tree.paste.PasteMinorMajorListChoiceToTrainingForm)

    def test_return_base_form_when_no_special_condition_met(self):
        path = "36"
        node_to_attach_from = NodeEducationGroupYearFactory(node_id=36)
        node_to_attach = NodeEducationGroupYearFactory()
        relationship_object = AuthorizedRelationshipObjectFactory(
            parent_type=node_to_attach_from.node_type,
            child_type=node_to_attach.node_type
        )
        self._mock_load_node(node_to_attach_from)
        self._mock_node_repo_get(node_to_attach)

        relationships = AuthorizedRelationshipListFactory(
            authorized_relationships=[relationship_object]
        )
        self._mock_load_authorized_relationships(relationships)

        form = program_management.forms.tree.paste.paste_form_factory(
            None,
            path,
            node_to_attach.code,
            node_to_attach.year
        )
        self.assertEqual(type(form), program_management.forms.tree.paste.PasteNodeForm)


class TestAttachNodeForm(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        root_node = NodeGroupYearFactory()
        cls.tree = ProgramTree(root_node)
        super().setUpClass()

    def _get_attach_node_form_instance(self, link_attributes=None):
        to_path = str(self.tree.root_node.pk)
        node_to_attach = NodeGroupYearFactory()

        return PasteNodeForm(
            to_path,
            node_to_attach.node_id,
            node_to_attach.node_type,
            data=link_attributes
        )

    def test_ensure_link_type_choice(self):
        form_instance = self._get_attach_node_form_instance({'link_type': 'invalid_link_type'})
        self.assertFalse(form_instance.is_valid())
        self.assertTrue(form_instance.errors['link_type'])

    def test_block_field_should_only_accept_sequence_of_increasing_digits_of_1_to_6(self):
        form_instance = self._get_attach_node_form_instance({'block': "012758"})
        self.assertTrue(form_instance.errors['block'])

        form_instance = self._get_attach_node_form_instance({'block': "125"})
        self.assertTrue(form_instance.is_valid())

    @mock.patch("program_management.ddd.service.write.paste_element_service.paste_element")
    def test_save_should_call_attach_service(self, mock_service_attach_node):
        form_instance = self._get_attach_node_form_instance(link_attributes={})
        form_instance.is_valid()
        form_instance.save()

        self.assertTrue(mock_service_attach_node.called)


class TestAttachNodeFormFields(SimpleTestCase):
    def test_attach_node_form_base_fields(self):
        node_to_attach = NodeEducationGroupYearFactory()
        form = program_management.forms.tree.paste.PasteNodeForm("", node_to_attach.node_id, node_to_attach.node_type)
        actual_fields = form.fields
        expected_fields = [
            'relative_credits',
            'access_condition',
            'is_mandatory',
            'block',
            'link_type',
            'comment',
            'comment_english'
        ]
        self.assertCountEqual(expected_fields, actual_fields)

    def test_attach_learning_unit_form_should_remove_access_condition_and_link_type_field(self):
        node_to_attach = NodeLearningUnitYearFactory()
        form = program_management.forms.tree.paste.PasteLearningUnitForm("", node_to_attach.node_id,
                                                                         node_to_attach.node_type)
        actual_fields = form.fields

        self.assertNotIn("access_condition", actual_fields)
        self.assertNotIn("link_type", actual_fields)

    def test_attach_to_minor_major_list_choice_should_remove_all_fields_but_access_condition(self):
        node_to_attach = NodeEducationGroupYearFactory()
        form = program_management.forms.tree.paste.PasteToMinorMajorListChoiceForm("", node_to_attach.node_id,
                                                                                   node_to_attach.node_type)
        actual_fields = form.fields
        expected_fields = ["access_condition"]

        self.assertCountEqual(actual_fields, expected_fields)

    def test_attach_minor_major_list_choice_to_training_form_should_disable_all_fields_but_block(self):
        node_to_attach = NodeEducationGroupYearFactory()
        form = program_management.forms.tree.paste.PasteMinorMajorListChoiceToTrainingForm("", node_to_attach.node_id,
                                                                                           node_to_attach.node_type)

        expected_fields_disabled = ["block"]
        actual_fields_disabled = [name for name, field in form.fields.items() if not field.disabled]
        self.assertCountEqual(expected_fields_disabled, actual_fields_disabled)

    def test_attach_not_authorized_children_should_remove_relative_credits_and_access_condition(self):
        node_to_attach = NodeEducationGroupYearFactory()
        form = program_management.forms.tree.paste.PasteNotAuthorizedChildren("", node_to_attach.node_id,
                                                                              node_to_attach.node_type)
        actual_fields = form.fields

        self.assertNotIn("access_condition", actual_fields)
        self.assertNotIn("relative_credits", actual_fields)
