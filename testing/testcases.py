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
import traceback
import warnings
from collections import namedtuple
from typing import Any, Optional, List

import mock
from django.test import TestCase

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from base.models.enums.education_group_types import EducationGroupTypesEnum
from education_group.ddd.domain.group import GroupIdentity
from education_group.tests.ddd.factories.repository.fake import get_fake_group_repository, \
    get_fake_mini_training_repository, get_fake_training_repository, FakeGroupRepository
from program_management.ddd.business_types import *
from program_management.tests.ddd.factories.authorized_relationship import AuthorizedRelationshipListFactory
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionFactory
from program_management.tests.ddd.factories.repository.fake import get_fake_program_tree_version_repository, \
    get_fake_program_tree_repository, get_fake_node_repository, FakeNodeRepository, FakeProgramTreeVersionRepository, \
    FakeProgramTreeRepository


class _AssertRaisesBusinessException:
    def __init__(self, expected, test_case):
        self.expected = expected
        self.test_case = test_case
        self.exception = None

    def _raise_failure(self, standard_msg):
        msg = self.test_case._formatMessage(None, standard_msg)
        raise self.test_case.failureException(msg)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is None:
            try:
                exc_name = self.expected.__name__
            except AttributeError:
                exc_name = str(self.expected)
            self._raise_failure("{} not raised".format(exc_name))
        else:
            traceback.clear_frames(exc_tb)
        if issubclass(exc_type, self.expected):
            self.exception = exc_value.with_traceback(None)
            return True
        elif issubclass(exc_type, MultipleBusinessExceptions):
            self.exception = exc_value.with_traceback(None)
            return self.expected in [type(exc) for exc in exc_value.exceptions]

        return False


# FIXME should herit from SimpleTestCase
class DDDTestCase(TestCase):
    starting_academic_year_year = 2020

    def setUp(self) -> None:
        super().setUp()
        self.mock_service(
            "base.models.academic_year.starting_academic_year",
            return_value=namedtuple("academic_year", "year")(self.starting_academic_year_year)
        )
        self._init_education_group_app_repo()
        self._init_program_management_app_repo()

    def _init_education_group_app_repo(self):
        self.fake_training_repository = get_fake_training_repository([])
        self.fake_mini_training_repository = get_fake_mini_training_repository([])
        self.fake_group_repository = get_fake_group_repository([])
        self.mock_repo("education_group.ddd.repository.group.GroupRepository", self.fake_group_repository)
        self.mock_repo("education_group.ddd.repository.training.TrainingRepository", self.fake_training_repository)
        self.mock_repo(
            "education_group.ddd.repository.mini_training.MiniTrainingRepository",
            self.fake_mini_training_repository
        )

    def _init_program_management_app_repo(self):
        self.fake_node_repository = get_fake_node_repository([])
        self.fake_program_tree_repository = get_fake_program_tree_repository([])
        self.fake_program_tree_version_repository = get_fake_program_tree_version_repository([])
        self.mock_repo(
            "program_management.ddd.repositories.node.NodeRepository",
            self.fake_node_repository
        )
        self.mock_repo(
            "program_management.ddd.repositories.program_tree.ProgramTreeRepository",
            self.fake_program_tree_repository
        )
        self.mock_repo(
            "program_management.ddd.repositories.program_tree_version.ProgramTreeVersionRepository",
            self.fake_program_tree_version_repository
        )
        self.mock_service(
            "program_management.ddd.repositories.load_authorized_relationship.load",
            return_value=AuthorizedRelationshipListFactory.load_from_fixture()
        )

        self.mock_service(
            "program_management.ddd.domain.service.identity_search.NodeIdentitySearch.get_from_element_id",
            side_effect=get_from_element_id
        )

        self.mock_service(
            "program_management.ddd.domain.service.node_identities_search.NodeIdentitiesSearch.search_from_code",
            side_effect=get_node_identities_from_code
        )

        self.mock_service(
            "program_management.ddd.domain.service.identity_search.ProgramTreeVersionIdentitySearch."
            "get_from_node_identities",
            side_effect=get_program_tree_version_identity_from_node_identities
        )

        self.mock_service(
            "education_group.ddd.domain.service.abbreviated_title_exist.CheckAcronymExist.exists",
            side_effect=check_acronym_exists
        )

        self.mock_service(
            "program_management.ddd.domain.service.identity_search.GroupIdentitySearch.get_from_tree_version_identity",
            side_effect=get_group_identity_from_tree_version_identity
        )

        self.mock_service(
            "program_management.ddd.domain.service.get_last_existing_version_name.GetLastExistingVersion."
            "get_last_existing_version_identity",
            side_effect=get_last_existing_version_identity
        )

        self.mock_service(
            "program_management.ddd.domain.service.generate_node_code.GenerateNodeCode._generate_node_code",
            side_effect=generate_node_code
        )
        self.mock_service(
            "program_management.ddd.domain.service.validation_rule.FieldValidationRule.get",
            side_effect=get_field_validation_rule
        )

        self.mock_service(
            "program_management.ddd.domain.service.get_next_version_if_exists.GetNextVersionIfExists"
            ".get_next_transition_version_year",
            side_effect=get_next_transition_version_year
        )

        self.mock_service(
            "program_management.ddd.domain.service.has_transition_version_with_greater_end_year"
            ".HasTransitionVersionWithGreaterEndYear.transition_version_greater_than_specific_version_year",
            side_effect=transition_version_greater_than_specific_version_year
        )

        self.mock_service(
            "program_management.ddd.domain.service.identity_search.ProgramTreeVersionIdentitySearch."
            "get_all_program_tree_version_identities",
            side_effect=get_all_program_tree_version_identities
        )

    def tearDown(self) -> None:
        self.fake_group_repository._groups = list()
        self.fake_mini_training_repository._mini_trainings = list()
        self.fake_training_repository._trainings = list()

        self.fake_node_repository._nodes = list()
        self.fake_program_tree_repository._trees = list()
        self.fake_program_tree_version_repository._trees_version = list()

    def mock_repo(self, repository_path: 'str', fake_repo: 'Any') -> mock.Mock:
        repository_patcher = mock.patch(repository_path, new=fake_repo)
        self.addCleanup(repository_patcher.stop)

        return repository_patcher.start()

    def mock_service(self, service_path: str, return_value: 'Any' = None, side_effect: 'Any' = None) -> mock.Mock:
        warnings.warn(
            "Deprecated an application service should not call an other application service. "
            "A domain service should not be mocked and should have it's repository injected.",
            DeprecationWarning,
            stacklevel=2
        )

        service_patcher = mock.patch(service_path, return_value=return_value, side_effect=side_effect)
        self.addCleanup(service_patcher.stop)

        return service_patcher.start()

    def add_node_to_repo(self, node: 'Node', create_tree_version=True, create_tree=True):
        self.fake_node_repository._nodes.append(node)

        if node.is_learning_unit():
            return

        tree_version = ProgramTreeVersionFactory(
            tree__root_node=node,
            entity_id__version_name=node.version_name
        )
        if create_tree_version:
            self.fake_program_tree_version_repository._trees_version.append(
                tree_version
            )
        if create_tree:
            self.fake_program_tree_repository._trees.append(
                tree_version.tree
            )

    def assertRaisesBusinessException(self, exception):
        """
        Assert that a business exception of exception type is raised.
        If a multiple business exception is raised, it will check that the exception
        is present in the list of exceptions.
        :param exception: A business exception type
        """
        return _AssertRaisesBusinessException(exception, self)


def get_from_element_id(element_id: int) -> Optional['NodeIdentity']:
    repo = FakeNodeRepository()
    return next(
        (node for node in repo._nodes if node.node_id == element_id),
        None
    )


def get_node_identities_from_code(group_code: str) -> List['NodeIdentity']:
    repo = FakeProgramTreeRepository()
    return [tree.root_node.entity_id for tree in repo._trees if tree.root_node.code == group_code]


def get_program_tree_version_identity_from_node_identities(
        node_identities: List['NodeIdentity']
) -> List['ProgramTreeVersionIdentity']:
    repo = FakeProgramTreeVersionRepository()
    node_identities_set = set(node_identities)
    return [
        tree_version.entity_id for tree_version in repo._trees_version
        if tree_version.get_tree().root_node.entity_id in node_identities_set
    ]


def get_group_identity_from_tree_version_identity(identity: 'ProgramTreeVersionIdentity') -> 'GroupIdentity':
    repo = FakeProgramTreeVersionRepository()
    return next(
        (GroupIdentity(code=tree_version.program_tree_identity.code, year=tree_version.program_tree_identity.year) for
         tree_version in repo._trees_version if tree_version.entity_id == identity),
        None
    )


def check_acronym_exists(abbreviated_title: str) -> bool:
    repo = FakeGroupRepository()
    return any(group for group in repo._groups if group.abbreviated_title == abbreviated_title)


def get_last_existing_version_identity(
        version_name: str,
        offer_acronym: str,
        transition_name: str,
) -> Optional['ProgramTreeVersionIdentity']:
    repo = FakeProgramTreeVersionRepository()
    existing_tree_version = repo.search(
        version_name=version_name,
        offer_acronym=offer_acronym,
        transition_name=transition_name
    )
    identities = [tree_version.entity_id for tree_version in existing_tree_version]
    identities_sorted_by_year = sorted(identities, key=lambda identity: identity.year, reverse=True)
    return next(iter(identities_sorted_by_year), None)


def generate_node_code(code, child_node_type):
    return code[:-1] + "X"


def get_next_transition_version_year(version: 'ProgramTreeVersion', initial_end_year: int) -> Optional[int]:
    repo = FakeProgramTreeVersionRepository()
    tree_versions = repo.search(version_name=version.version_name, offer_acronym=version.entity_id.offer_acronym)
    transitions = (tree_version for tree_version in tree_versions if tree_version.is_transition)
    transitions_year_in_range_year = (
        transition.entity_id.year for transition in transitions if
        initial_end_year < transition.entity_id.year <= version.end_year_of_existence
    )
    return min(transitions_year_in_range_year, default=None)


def transition_version_greater_than_specific_version_year(specific_version: 'ProgramTreeVersion') -> bool:
    repo = FakeProgramTreeVersionRepository()
    tree_versions = repo.search(
        version_name=specific_version.version_name,
        offer_acronym=specific_version.entity_id.offer_acronym
    )
    transitions_year = (tree_version.entity_id.year for tree_version in tree_versions if tree_version.is_transition)
    return max(transitions_year, default=specific_version.entity_id.year) > specific_version.entity_id.year


def get_all_program_tree_version_identities(
        program_tree_version_identity: 'ProgramTreeVersionIdentity'
) -> List['ProgramTreeVersionIdentity']:
    repo = FakeProgramTreeVersionRepository()
    return [
        tree_version.entity_id for tree_version in repo._trees_version
        if (tree_version.entity_id.version_name,
            tree_version.entity_id.transition_name,
            tree_version.entity_id.offer_acronym) == (
           program_tree_version_identity.version_name,
           program_tree_version_identity.transition_name,
           program_tree_version_identity.offer_acronym)
    ]


def get_field_validation_rule(node_type: EducationGroupTypesEnum, field_name: str, is_version: bool = False):
    if field_name == "title_fr":
        return namedtuple("Title", "initial_value")("TitleFR")
    elif field_name == 'abbreviated_title':
        return namedtuple("AbbreviatedTitle", "initial_value")("AbbrevTitle")
    return namedtuple("Credits", "initial_value")(15)
