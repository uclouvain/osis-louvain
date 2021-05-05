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
import itertools
from typing import Dict, List

import factory.fuzzy

from program_management.ddd import command
from program_management.ddd.domain.program_tree import ProgramTree, ProgramTreeIdentity
from program_management.ddd.repositories import program_tree as program_tree_repository
from program_management.ddd.service.write import copy_program_tree_service
from program_management.models.enums.node_type import NodeType
from program_management.tests.ddd.factories.authorized_relationship import AuthorizedRelationshipListFactory
from program_management.tests.ddd.factories.domain.prerequisite.prerequisite import PrerequisitesFactory
from program_management.tests.ddd.factories.link import LinkFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory, NodeLearningUnitYearFactory


class ProgramTreeIdentityFactory(factory.Factory):

    class Meta:
        model = ProgramTreeIdentity
        abstract = False

    code = factory.Sequence(lambda n: 'CODE%02d' % n)
    year = factory.fuzzy.FuzzyInteger(low=1999, high=2099)


class ProgramTreeFactory(factory.Factory):

    class Meta:
        model = ProgramTree
        abstract = False

    root_node = factory.SubFactory(NodeGroupYearFactory)
    authorized_relationships = factory.SubFactory(
        AuthorizedRelationshipListFactory,
    )
    entity_id = factory.SubFactory(
        ProgramTreeIdentityFactory,
        code=factory.SelfAttribute("..root_node.code"),
        year=factory.SelfAttribute("..root_node.year")
    )
    prerequisites = factory.SubFactory(
        PrerequisitesFactory,
        context_tree=factory.SelfAttribute("..entity_id")
    )

    class Params:
        load_fixture = factory.Trait(
            authorized_relationships=AuthorizedRelationshipListFactory.load_from_fixture()
        )

    @factory.post_generation
    def persist(obj, create, extracted, **kwargs):
        if extracted:
            program_tree_repository.ProgramTreeRepository.create(obj)


def _tree_builder(data: Dict, nodes_generated: Dict, persist: bool = False) -> 'Node':
    _data = data.copy()
    children = _data.pop("children", [])

    if _data["code"] in nodes_generated:
        return nodes_generated[_data["code"]]

    node = _node_builder(_data, persist=persist)
    nodes_generated[node.code] = node

    for child_data, order in zip(children, itertools.count()):
        link_data = child_data.pop("link_data", {})
        child_node = _tree_builder(child_data, nodes_generated, persist=persist)
        LinkFactory(parent=node, child=child_node, **link_data, order=order)

    return node


def _node_builder(data: Dict, persist: bool = False) -> 'Node':
    node_factory = NodeGroupYearFactory
    if data["node_type"] == NodeType.LEARNING_UNIT:
        node_factory = NodeLearningUnitYearFactory
    return node_factory(**data, persist=persist)


def tree_builder(data: Dict, persist: bool = False) -> 'ProgramTree':
    root_node = _tree_builder(data, {}, persist)
    authorized_relationships = AuthorizedRelationshipListFactory.load_from_fixture()
    return ProgramTreeFactory(root_node=root_node, authorized_relationships=authorized_relationships, persist=persist)