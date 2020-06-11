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
from unittest import skip, mock

import factory.fuzzy
from django.test import SimpleTestCase, TestCase
from django.utils.translation import gettext as _

from base.models.enums.education_group_types import GroupType, MiniTrainingType
from base.models.enums.link_type import LinkTypes
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group_year import TrainingFactory, MiniTrainingFactory, EducationGroupYearFactory, \
    GroupFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.forms.tree import attach
from program_management.forms.tree.attach import AttachNodeForm, GroupElementYearForm
from program_management.models.enums.node_type import NodeType
from program_management.tests.ddd.factories.authorized_relationship import AuthorizedRelationshipListFactory, \
    AuthorizedRelationshipObjectFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory, \
    NodeEducationGroupYearFactory


class TestAttachNodeFormFactory(SimpleTestCase):
    def _mock_load_by_type(self, return_values):
        patcher_load = mock.patch("program_management.ddd.repositories.load_node.load_by_type")
        self.addCleanup(patcher_load.stop)
        self.mock_load = patcher_load.start()
        self.mock_load.side_effect = return_values

    def _mock_load_authorized_relationships(self, return_value):
        patcher_load = mock.patch("program_management.ddd.repositories.load_authorized_relationship.load")
        self.addCleanup(patcher_load.stop)
        self.mock_load = patcher_load.start()
        self.mock_load.return_value = return_value

    def test_form_returned_when_child_node_is_a_learning_unit(self):
        path = "1|2"
        node_to_attach_from = NodeEducationGroupYearFactory(node_id=2)
        node_to_attach = NodeLearningUnitYearFactory()
        self._mock_load_by_type([node_to_attach_from, node_to_attach])

        relationships = AuthorizedRelationshipListFactory()
        self._mock_load_authorized_relationships(relationships)

        form = attach.attach_form_factory(None, path, node_to_attach.node_id, node_to_attach.node_type)
        self.assertIsInstance(form, attach.AttachLearningUnitForm)

    def test_form_returned_when_relationship_is_not_authorized(self):
        path = "9|4|5"
        node_to_attach_from = NodeEducationGroupYearFactory(node_id=5)
        node_to_attach = NodeEducationGroupYearFactory(node_type=MiniTrainingType.FSA_SPECIALITY)
        self._mock_load_by_type([node_to_attach_from, node_to_attach])

        relationships = AuthorizedRelationshipListFactory(
            authorized_relationships=[AuthorizedRelationshipObjectFactory(child_type=MiniTrainingType.SOCIETY_MINOR)]
        )
        self._mock_load_authorized_relationships(relationships)

        form = attach.attach_form_factory(None, path, node_to_attach.node_id, node_to_attach.node_type)
        self.assertIsInstance(form, attach.AttachNotAuthorizedChildren)

    def test_form_returned_when_parent_is_minor_major_list_choice(self):
        path = "6"
        node_to_attach_from = NodeEducationGroupYearFactory(
            node_type=factory.fuzzy.FuzzyChoice(GroupType.minor_major_list_choice_enums()),
            node_id=6
        )
        node_to_attach = NodeEducationGroupYearFactory()
        self._mock_load_by_type([node_to_attach_from, node_to_attach])

        relationship_object = AuthorizedRelationshipObjectFactory(
            parent_type=node_to_attach_from.node_type,
            child_type=node_to_attach.node_type
        )
        relationships = AuthorizedRelationshipListFactory(
            authorized_relationships=[relationship_object]
        )
        self._mock_load_authorized_relationships(relationships)

        form = attach.attach_form_factory(None, path, node_to_attach.node_id, node_to_attach.node_type)
        self.assertIsInstance(form, attach.AttachToMinorMajorListChoiceForm)

    def test_form_returned_when_parent_is_training_and_child_is_minor_major_list_choice(self):
        path = "65|589"
        node_to_attach_from = NodeEducationGroupYearFactory()
        node_to_attach = NodeEducationGroupYearFactory(
            node_type=factory.fuzzy.FuzzyChoice(GroupType.minor_major_list_choice_enums())
        )
        self._mock_load_by_type([node_to_attach_from, node_to_attach])

        relationship_object = AuthorizedRelationshipObjectFactory(
            parent_type=node_to_attach_from.node_type,
            child_type=node_to_attach.node_type
        )
        relationships = AuthorizedRelationshipListFactory(
            authorized_relationships=[relationship_object]
        )
        self._mock_load_authorized_relationships(relationships)

        form = attach.attach_form_factory(None, path, node_to_attach.node_id, node_to_attach.node_type)
        self.assertIsInstance(form, attach.AttachMinorMajorListChoiceToTrainingForm)

    def test_return_base_form_when_no_special_condition_met(self):
        path = "36"
        node_to_attach_from = NodeEducationGroupYearFactory(node_id=36)
        node_to_attach = NodeEducationGroupYearFactory()
        relationship_object = AuthorizedRelationshipObjectFactory(
            parent_type=node_to_attach_from.node_type,
            child_type=node_to_attach.node_type
        )
        self._mock_load_by_type([node_to_attach_from, node_to_attach])

        relationships = AuthorizedRelationshipListFactory(
            authorized_relationships=[relationship_object]
        )
        self._mock_load_authorized_relationships(relationships)

        form = attach.attach_form_factory(None, path, node_to_attach.node_id, node_to_attach.node_type)
        self.assertEqual(type(form), attach.AttachNodeForm)


class TestAttachNodeForm(SimpleTestCase):
    @classmethod
    def setUpClass(cls):
        root_node = NodeGroupYearFactory()
        cls.tree = ProgramTree(root_node)
        super().setUpClass()

    def _get_attach_node_form_instance(self, link_attributes=None):
        to_path = str(self.tree.root_node.pk)
        node_to_attach = NodeGroupYearFactory()

        return AttachNodeForm(
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

    @mock.patch("program_management.ddd.service.attach_node_service.attach_node")
    def test_save_should_call_attach_service(self, mock_service_attach_node):
        form_instance = self._get_attach_node_form_instance(link_attributes={})
        form_instance.is_valid()
        form_instance.save()

        self.assertTrue(mock_service_attach_node.called)


class TestAttachNodeFormFields(SimpleTestCase):
    def test_attach_node_form_base_fields(self):
        node_to_attach = NodeEducationGroupYearFactory()
        form = attach.AttachNodeForm("", node_to_attach.node_id, node_to_attach.node_type)
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
        form = attach.AttachLearningUnitForm("", node_to_attach.node_id, node_to_attach.node_type)
        actual_fields = form.fields

        self.assertNotIn("access_condition", actual_fields)
        self.assertNotIn("link_type", actual_fields)

    def test_attach_to_minor_major_list_choice_should_remove_all_fields_but_access_condition(self):
        node_to_attach = NodeEducationGroupYearFactory()
        form = attach.AttachToMinorMajorListChoiceForm("", node_to_attach.node_id, node_to_attach.node_type)
        actual_fields = form.fields
        expected_fields = ["access_condition"]

        self.assertCountEqual(actual_fields, expected_fields)

    def test_attach_minor_major_list_choice_to_training_form_should_disable_all_fields_but_block(self):
        node_to_attach = NodeEducationGroupYearFactory()
        form = attach.AttachMinorMajorListChoiceToTrainingForm("", node_to_attach.node_id, node_to_attach.node_type)

        expected_fields_disabled = ["block"]
        actual_fields_disabled = [name for name, field in form.fields.items() if not field.disabled]
        self.assertCountEqual(expected_fields_disabled, actual_fields_disabled)

    def test_attach_not_authorized_children_should_remove_relative_credits_and_access_condition(self):
        node_to_attach = NodeEducationGroupYearFactory()
        form = attach.AttachNotAuthorizedChildren("", node_to_attach.node_id, node_to_attach.node_type)
        actual_fields = form.fields

        self.assertNotIn("access_condition", actual_fields)
        self.assertNotIn("relative_credits", actual_fields)


class TestGroupElementYearForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        cls.parent = TrainingFactory(
            academic_year=cls.academic_year,
            education_group_type__learning_unit_child_allowed=True
        )
        cls.child_leaf = LearningUnitYearFactory()
        cls.child_branch = MiniTrainingFactory(academic_year=cls.academic_year)

    def test_fields_relevant(self):
        form = GroupElementYearForm()

        expected_fields = {
            "relative_credits",
            "is_mandatory",
            "block",
            "link_type",
            "comment",
            "comment_english",
            "access_condition"
        }
        self.assertFalse(expected_fields.symmetric_difference(set(form.fields.keys())))

    @skip
    def test_clean_link_type_reference_between_eg_lu(self):
        form = GroupElementYearForm(
            data={'link_type': LinkTypes.REFERENCE.name},
            parent=self.parent,
            child_leaf=self.child_leaf
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue("link_type" not in form.fields)

    def test_clean_link_type_reference_with_authorized_relationship(self):
        AuthorizedRelationshipFactory(
            parent_type=self.parent.education_group_type,
            child_type=self.child_branch.education_group_type,
        )
        ref_group = GroupElementYearFactory(
            parent=self.child_branch,
            child_branch=EducationGroupYearFactory(
                academic_year=self.academic_year,
                education_group_type=self.child_branch.education_group_type
            )
        )
        AuthorizedRelationshipFactory(
            parent_type=self.parent.education_group_type,
            child_type=ref_group.child_branch.education_group_type,
        )

        form = GroupElementYearForm(
            data={'link_type': LinkTypes.REFERENCE.name},
            parent=self.parent,
            child_branch=self.child_branch
        )

        self.assertTrue(form.is_valid())

    def test_remove_access_condition_when_not_authorized_relationship(self):
        form = GroupElementYearForm(parent=self.parent, child_branch=self.child_branch)
        self.assertTrue("access_condition" not in list(form.fields.keys()))

    def test_only_keep_access_condition_when_parent_is_minor_major_option_list_choice(self):
        expected_fields = ["access_condition"]
        for name in GroupType.minor_major_option_list_choice():
            with self.subTest(type=name):
                parent = GroupFactory(education_group_type__name=name)
                AuthorizedRelationshipFactory(
                    parent_type=parent.education_group_type,
                    child_type=self.child_branch.education_group_type
                )
                form = GroupElementYearForm(parent=parent, child_branch=self.child_branch)
                self.assertCountEqual(expected_fields, list(form.fields.keys()))

    def test_disable_all_fields_except_block_when_parent_is_formation_and_child_is_minor_major_option_list_choice(self):
        expected_fields = [
            "block"
        ]
        for name in GroupType.minor_major_option_list_choice():
            with self.subTest(type=name):
                child_branch = GroupFactory(education_group_type__name=name)
                AuthorizedRelationshipFactory(
                    parent_type=self.parent.education_group_type,
                    child_type=child_branch.education_group_type
                )
                form = GroupElementYearForm(parent=self.parent, child_branch=child_branch)
                enabled_fields = [name for name, field in form.fields.items() if not field.disabled]
                self.assertCountEqual(expected_fields, enabled_fields)

    def test_remove_access_condition_when_authorized_relationship(self):
        AuthorizedRelationshipFactory(
            parent_type=self.parent.education_group_type,
            child_type=self.child_branch.education_group_type
        )
        form = GroupElementYearForm(parent=self.parent, child_branch=self.child_branch)
        self.assertTrue("access_condition" not in list(form.fields.keys()))

    def test_child_education_group_year_without_authorized_relationship_fails(self):
        form = GroupElementYearForm(
            data={'link_type': ""},
            parent=self.parent,
            child_branch=self.child_branch
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["link_type"],
            [_("You cannot add \"%(child_types)s\" to \"%(parent)s\" (type \"%(parent_type)s\")") % {
                 'child_types': self.child_branch.education_group_type,
                 'parent': self.parent,
                 'parent_type': self.parent.education_group_type,
             }]
        )

    def test_initial_value_relative_credits(self):
        form = GroupElementYearForm(parent=self.parent, child_branch=self.child_branch)
        self.assertEqual(form.initial['relative_credits'], self.child_branch.credits)

        form = GroupElementYearForm(parent=self.parent, child_leaf=self.child_leaf)
        self.assertEqual(form.initial['relative_credits'], self.child_leaf.credits)

        form = GroupElementYearForm(parent=self.parent)
        self.assertEqual(form.initial['relative_credits'], None)
