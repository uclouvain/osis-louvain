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
from unittest import mock

import attr
from django.test import SimpleTestCase

import program_management.ddd.command
import program_management.ddd.service.write.paste_element_service
from base.models.authorized_relationship import AuthorizedRelationshipObject
from base.models.enums.education_group_types import TrainingType, GroupType, MiniTrainingType
from base.models.enums.link_type import LinkTypes
from osis_common.ddd.interface import BusinessExceptions
from program_management.ddd.domain import exception
from program_management.ddd.repositories import node as node_repositoriy
from program_management.ddd.service.read import check_paste_node_service
from program_management.ddd.service.write import paste_element_service
from program_management.ddd.validators.validators_by_business_action import CheckPasteNodeValidatorList
from program_management.models.enums.node_type import NodeType
from program_management.tests.ddd.factories.commands.paste_element_command import PasteElementCommandFactory
from program_management.tests.ddd.factories.domain.program_tree.BACHELOR_1BA import ProgramTreeBachelorFactory
from program_management.tests.ddd.factories.domain.program_tree.MASTER_2M import ProgramTree2MFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory, tree_builder
from program_management.tests.ddd.factories.program_tree_version import StandardProgramTreeVersionFactory
from program_management.tests.ddd.factories.repository.fake import get_fake_program_tree_repository, \
    get_fake_node_repository, get_fake_program_tree_version_repository
from program_management.tests.ddd.service.mixins import ValidatorPatcherMixin
from testing.mocks import MockPatcherMixin
from testing.testcases import DDDTestCase


class TestPasteLearningUnitNodeService(DDDTestCase, MockPatcherMixin):
    def setUp(self) -> None:
        self.tree = ProgramTreeBachelorFactory(2020, 2025)
        self.tree_version = StandardProgramTreeVersionFactory(tree=self.tree)

        self.fake_program_tree_repository = get_fake_program_tree_repository([self.tree])
        self.mock_repo(
            "program_management.ddd.repositories.program_tree.ProgramTreeRepository",
            self.fake_program_tree_repository
        )

        self.fake_tree_version_repository = get_fake_program_tree_version_repository([self.tree_version])
        self.mock_repo(
            "program_management.ddd.repositories.program_tree_version.ProgramTreeVersionRepository",
            self.fake_tree_version_repository
        )

        self.node_to_paste = NodeLearningUnitYearFactory()

        self.fake_node_repository = get_fake_node_repository([self.node_to_paste])
        self.mock_repo(
            "program_management.ddd.repositories.node.NodeRepository",
            self.fake_node_repository
        )

        self.mocked_get_from_element_id = self.mock_get_program_tree_identity_from_element_id()
        self.mocked_get_from_element_id.return_value = self.tree.entity_id

    def mock_get_program_tree_identity_from_element_id(self):
        pacher = mock.patch("program_management.ddd.domain.service."
                            "identity_search.ProgramTreeIdentitySearch.get_from_element_id")
        mocked_method = pacher.start()
        self.addCleanup(pacher.stop)
        return mocked_method

    def test_cannot_paste_to_learning_unit_node(self):
        invalid_where_to_paste_path_command = PasteElementCommandFactory(
            node_to_paste_code=self.node_to_paste.code,
            node_to_paste_year=self.node_to_paste.year,
            path_where_to_paste="1|21|31|41",
        )
        self.assertRaisesBusinessException(
            exception.CannotPasteToLearningUnitException,
            paste_element_service.paste_element,
            invalid_where_to_paste_path_command
        )

    def test_block_should_be_empty_or_a_sequence_of_increasing_digit_comprised_between_1_and_6(self):
        invalid_block_command = PasteElementCommandFactory(
            node_to_paste_code=self.node_to_paste.code,
            node_to_paste_year=self.node_to_paste.year,
            path_where_to_paste="1",
            block="1298"
        )

        self.assertRaisesBusinessException(
            exception.InvalidBlockException,
            paste_element_service.paste_element,
            invalid_block_command
        )

    def test_cannot_create_a_reference_link_with_a_learning_unit(self):
        invalid_command = PasteElementCommandFactory(
            node_to_paste_code=self.node_to_paste.code,
            node_to_paste_year=self.node_to_paste.year,
            path_where_to_paste="1",
            link_type=LinkTypes.REFERENCE.name
        )

        self.assertRaisesBusinessException(
            exception.ReferenceLinkNotAllowedWithLearningUnitException,
            paste_element_service.paste_element,
            invalid_command
        )

    def test_cannot_paste_learning_unit_to_parent_dont_allow(self):
        invalid_command = PasteElementCommandFactory(
            node_to_paste_code=self.node_to_paste.code,
            node_to_paste_year=self.node_to_paste.year,
            path_where_to_paste="1|21",
        )

        self.assertRaisesBusinessException(
            exception.ChildTypeNotAuthorizedException,
            paste_element_service.paste_element,
            invalid_command
        )

    def test_cannot_paste_if_do_not_allow_referenced_children(self):
        tree_data = {
            "node_type": GroupType.SUB_GROUP,
            "year": 2020,
            "end_year": 2025,
            "node_id": 100,
            "children": [
                {
                    "node_type": NodeType.LEARNING_UNIT,
                    "year": 2020,
                    "end_date": 2025,
                    "node_id": 101,
                }
            ]
        }
        tree_to_paste = tree_builder(tree_data)
        self.fake_program_tree_repository.root_entities.append(tree_to_paste)

        invalid_command = PasteElementCommandFactory(
            node_to_paste_code=tree_to_paste.root_node.code,
            node_to_paste_year=tree_to_paste.root_node.year,
            path_where_to_paste="1|21",
            link_type=LinkTypes.REFERENCE.name
        )

        self.assertRaisesBusinessException(
            exception.ChildTypeNotAuthorizedException,
            paste_element_service.paste_element,
            invalid_command
        )


class TestPasteGroupNodeService(DDDTestCase, MockPatcherMixin):
    def setUp(self) -> None:
        self.tree = ProgramTreeBachelorFactory(2020, 2025)

        tree_to_paste_data = {
            "node_type": MiniTrainingType.OPTION,
            "year": 2020
        }
        self.tree_to_paste = tree_builder(tree_to_paste_data)
        self.node_to_paste = self.tree_to_paste.root_node

        self.fake_program_tree_repository = get_fake_program_tree_repository([self.tree, self.tree_to_paste])
        self.tree_version = StandardProgramTreeVersionFactory(
            tree=self.tree,
            program_tree_repository=self.fake_program_tree_repository
        )
        self.tree_version_to_paste = StandardProgramTreeVersionFactory(
            tree=self.tree_to_paste,
            program_tree_repository=self.fake_program_tree_repository
        )
        self.mock_repo(
            "program_management.ddd.repositories.program_tree.ProgramTreeRepository",
            self.fake_program_tree_repository
        )

        self.fake_tree_version_repository = get_fake_program_tree_version_repository(
            [self.tree_version, self.tree_version_to_paste]
        )
        self.mock_repo(
            "program_management.ddd.repositories.program_tree_version.ProgramTreeVersionRepository",
            self.fake_tree_version_repository
        )

        self.fake_node_repository = get_fake_node_repository([self.node_to_paste])
        self.mock_repo(
            "program_management.ddd.repositories.node.NodeRepository",
            self.fake_node_repository
        )

        self.mocked_get_from_element_id = self.mock_get_program_tree_identity_from_element_id()
        self.mocked_get_from_element_id.return_value = self.tree.entity_id

    def mock_get_program_tree_identity_from_element_id(self):
        pacher = mock.patch("program_management.ddd.domain.service."
                            "identity_search.ProgramTreeIdentitySearch.get_from_element_id")
        mocked_method = pacher.start()
        self.addCleanup(pacher.stop)
        return mocked_method

    def test_can_not_attach_the_same_node_to_same_parent(self):
        node_attached_to_root = self.tree.get_node("1|22")
        tree_to_attach = ProgramTreeFactory(root_node=node_attached_to_root)
        self.fake_node_repository.root_entities.append(node_attached_to_root)
        self.fake_program_tree_repository.root_entities.append(tree_to_attach)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_attach,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )

        invalid_where_to_paste_path_command = PasteElementCommandFactory(
            node_to_paste_code=node_attached_to_root.code,
            node_to_paste_year=node_attached_to_root.year,
            path_where_to_paste="1|22",
        )

        self.assertRaisesBusinessException(
            exception.CannotPasteNodeToHimselfException,
            paste_element_service.paste_element,
            invalid_where_to_paste_path_command
        )

    def test_block_should_be_empty_or_a_sequence_of_increasing_digit_comprised_between_1_and_6(self):
        invalid_block_command = PasteElementCommandFactory(
            node_to_paste_code=self.node_to_paste.code,
            node_to_paste_year=self.node_to_paste.year,
            path_where_to_paste="1|22",
            block="1298"
        )

        self.assertRaisesBusinessException(
            exception.InvalidBlockException,
            paste_element_service.paste_element,
            invalid_block_command
        )

    def test_cannot_paste_group_type_to_parent_who_dont_allow(self):
        invalid_command = PasteElementCommandFactory(
            node_to_paste_code=self.node_to_paste.code,
            node_to_paste_year=self.node_to_paste.year,
            path_where_to_paste="1|22",
        )

        self.assertRaisesBusinessException(
            exception.ChildTypeNotAuthorizedException,
            paste_element_service.paste_element,
            invalid_command
        )

    def test_cannot_paste_group_if_not_same_academic_year_than_parent(self):
        self.node_to_paste.year = 2021
        self.node_to_paste.entity_id = attr.evolve(self.node_to_paste.entity_id, year=2021)
        tree_to_paste = ProgramTreeFactory(root_node=self.node_to_paste)
        self.fake_program_tree_repository.root_entities.append(tree_to_paste)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_paste,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )

        invalid_command = PasteElementCommandFactory(
            node_to_paste_code=self.node_to_paste.code,
            node_to_paste_year=self.node_to_paste.year,
            path_where_to_paste="1|22",
        )

        self.assertRaisesBusinessException(
            exception.ParentAndChildMustHaveSameAcademicYearException,
            paste_element_service.paste_element,
            invalid_command
        )

    def test_cannot_paste_if_reference_link_and_referenced_children_are_not_allowed(self):
        tree_to_paste = tree_builder(
            {
                "node_type": GroupType.MINOR_LIST_CHOICE,
                "year": 2020,
                "children": [
                    {"node_type": NodeType.LEARNING_UNIT},
                    {"node_type": GroupType.SUB_GROUP, "year": 2020}
                ]
            }
        )
        self.fake_program_tree_repository.root_entities.append(tree_to_paste)
        self.fake_node_repository.root_entities.append(tree_to_paste.root_node)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_paste,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )

        invalid_command = PasteElementCommandFactory(
            node_to_paste_code=tree_to_paste.root_node.code,
            node_to_paste_year=tree_to_paste.root_node.year,
            path_where_to_paste="1",
            link_type=LinkTypes.REFERENCE.name
        )

        self.assertRaisesBusinessException(
            exception.ChildTypeNotAuthorizedException,
            paste_element_service.paste_element,
            invalid_command
        )

    def test_can_paste_if_referenced_children_allowed(self):
        tree_to_paste = tree_builder(
            {
                "node_type": GroupType.SUB_GROUP,
                "year": 2020,
                "children": [
                    {"node_type": NodeType.LEARNING_UNIT},
                    {"node_type": GroupType.MINOR_LIST_CHOICE, "year": 2020}
                ]
            }
        )
        self.fake_program_tree_repository.root_entities.append(tree_to_paste)
        self.fake_node_repository.root_entities.append(tree_to_paste.root_node)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_paste,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )

        valid_command = PasteElementCommandFactory(
            node_to_paste_code=tree_to_paste.root_node.code,
            node_to_paste_year=tree_to_paste.root_node.year,
            path_where_to_paste="1",
            link_type=LinkTypes.REFERENCE.name
        )

        result = paste_element_service.paste_element(valid_command)
        self.assertTrue(result)

    def test_cannot_paste_if_maximum_child_of_type_reached(self):
        self.tree.authorized_relationships.update(
            TrainingType.BACHELOR, GroupType.COMMON_CORE, max_count_authorized=1
        )
        tree_to_paste_data = {
            "node_type": GroupType.COMMON_CORE,
            "year": 2020
        }
        tree_to_paste = tree_builder(tree_to_paste_data)
        node_to_paste = tree_to_paste.root_node

        self.fake_program_tree_repository.root_entities.append(tree_to_paste)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_paste,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )

        invalid_command = PasteElementCommandFactory(
            node_to_paste_code=node_to_paste.code,
            node_to_paste_year=node_to_paste.year,
            path_where_to_paste="1",
        )

        self.assertRaisesBusinessException(
            exception.MaximumChildTypesReachedException,
            paste_element_service.paste_element,
            invalid_command
        )

    def test_should_let_paste_list_minor_major_inside_list_minor_major(self):
        tree_to_paste_data = {
            "node_type": GroupType.MINOR_LIST_CHOICE,
            "year": 2020,
            "children": [
                {
                    "node_type": MiniTrainingType.OPEN_MINOR,
                    "year": 2020,
                    "end_year": 2025,
                    "link_data": {"link_type": LinkTypes.REFERENCE},
                    "children": [
                        {
                            "node_type": GroupType.COMMON_CORE,
                            "year": 2020
                        }
                    ]
                },
            ]
        }
        tree_to_paste = tree_builder(tree_to_paste_data)
        self.fake_program_tree_repository.root_entities.append(tree_to_paste)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_paste,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )

        valid_command = PasteElementCommandFactory(
            node_to_paste_code=tree_to_paste.root_node.code,
            node_to_paste_year=tree_to_paste.root_node.year,
            path_where_to_paste="1|22",
            link_type=None
        )

        result = paste_element_service.paste_element(valid_command)
        self.assertTrue(result)

    def test_should_set_link_as_not_mandatory_when_parent_is_list_minor_major_list_or_option_choice(self):
        tree_to_paste_data = {
            "node_type": MiniTrainingType.OPEN_MINOR,
            "year": 2020,
            "node_id": 589
        }
        tree_to_paste = tree_builder(tree_to_paste_data)
        self.fake_program_tree_repository.root_entities.append(tree_to_paste)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_paste,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )

        valid_command = PasteElementCommandFactory(
            node_to_paste_code=tree_to_paste.root_node.code,
            node_to_paste_year=tree_to_paste.root_node.year,
            path_where_to_paste="1|22",
            link_type=None,
            is_mandatory=True
        )
        paste_element_service.paste_element(valid_command)

        created_link = self.tree.get_link(
            self.tree.get_node("1|22"),
            self.tree.get_node("1|22|589")
        )
        self.assertFalse(created_link.is_mandatory)

    def test_cannot_paste_list_finalities_inside_list_finalities_if_max_finalities_is_surpassed(self):
        tree_to_paste_data = {
            "node_type": GroupType.FINALITY_120_LIST_CHOICE,
            "year": 2020,
            "children": [
                {
                    "node_type": TrainingType.MASTER_MD_120,
                    "year": 2020,
                    "end_year": 2025
                },
            ]
        }

        tree = ProgramTree2MFactory(2020, 2025)
        tree_to_paste = tree_builder(tree_to_paste_data)

        self.fake_program_tree_repository.root_entities.append(tree_to_paste)
        self.fake_program_tree_repository.root_entities.append(tree)
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree_to_paste,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )
        self.fake_tree_version_repository.root_entities.append(
            StandardProgramTreeVersionFactory(
                tree=tree,
                program_tree_repository=self.fake_program_tree_repository,
            )
        )
        tree.authorized_relationships.update(
            parent_type=GroupType.FINALITY_120_LIST_CHOICE,
            child_type=TrainingType.MASTER_MD_120,
            min_count_authorized=1,
            max_count_authorized=1
        )
        tree.authorized_relationships.authorized_relationships.append(
            AuthorizedRelationshipObject(
                parent_type=GroupType.FINALITY_120_LIST_CHOICE,
                child_type=GroupType.FINALITY_120_LIST_CHOICE,
                min_count_authorized=0,
                max_count_authorized=None
            )
        )

        self.mocked_get_from_element_id.return_value = tree.entity_id

        invalid_command = PasteElementCommandFactory(
            node_to_paste_code=tree_to_paste.root_node.code,
            node_to_paste_year=tree_to_paste.root_node.year,
            path_where_to_paste="1|22",
        )

        self.assertRaisesBusinessException(
            exception.MaximumChildTypesReachedException,
            paste_element_service.paste_element,
            invalid_command
        )


class TestCheckPaste(SimpleTestCase, ValidatorPatcherMixin):
    def setUp(self) -> None:
        self.tree = ProgramTreeFactory()
        self.node_to_attach_from = NodeGroupYearFactory()
        LinkFactory(parent=self.tree.root_node, child=self.node_to_attach_from)
        self.path = "|".join([str(self.tree.root_node.node_id), str(self.node_to_attach_from.node_id)])

        self.node_to_paste = NodeGroupYearFactory()

        self._patch_load_tree()
        self._patch_load_node()
        self._patch_get_node_from_element_id()
        self.mock_check_paste_validator = self._path_validator()

    def _patch_load_node(self):
        patcher_load_nodes = mock.patch.object(
            node_repositoriy.NodeRepository,
            "get"
        )
        self.mock_load_node = patcher_load_nodes.start()
        self.mock_load_node.return_value = self.node_to_paste
        self.addCleanup(patcher_load_nodes.stop)

    def _patch_load_tree(self):
        patcher_load_tree = mock.patch(
            "program_management.ddd.repositories.program_tree.ProgramTreeRepository.get"
        )
        self.mock_load_tree = patcher_load_tree.start()
        self.mock_load_tree.return_value = self.tree
        self.addCleanup(patcher_load_tree.stop)

    def _patch_get_node_from_element_id(self):
        patcher_load_tree = mock.patch(
            "program_management.ddd.domain.service.identity_search.NodeIdentitySearch.get_from_element_id"
        )
        self.mock_load_tree = patcher_load_tree.start()
        self.mock_load_tree.return_value = self.tree.root_node
        self.addCleanup(patcher_load_tree.stop)

    def _path_validator(self):
        patch_validator = mock.patch.object(
            CheckPasteNodeValidatorList, "validate"
        )
        mock_validator = patch_validator.start()
        mock_validator.return_value = True
        self.addCleanup(patch_validator.stop)
        return mock_validator

    def test_should_propagate_error_when_validator_raises_exception(self):
        self.mock_check_paste_validator.side_effect = BusinessExceptions(["an error"])
        check_command = program_management.ddd.command.CheckPasteNodeCommand(
            root_id=self.tree.root_node.node_id,
            node_to_past_code=self.node_to_paste.code,
            node_to_paste_year=self.node_to_paste.year,
            path_to_paste=self.path,
            path_to_detach=None
        )
        with self.assertRaises(BusinessExceptions):
            check_paste_node_service.check_paste(check_command)

    def test_should_return_none_when_validator_do_not_raise_exception(self):
        check_command = program_management.ddd.command.CheckPasteNodeCommand(
            root_id=self.tree.root_node.node_id,
            node_to_past_code=self.node_to_paste.code,
            node_to_paste_year=self.node_to_paste.year,
            path_to_paste=self.path,
            path_to_detach=None
        )
        self.assertIsNone(check_paste_node_service.check_paste(check_command))
