#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import attr

from education_group.ddd.service.write import copy_group_service
from program_management.ddd.command import FillProgramTreeContentFromLastYearCommand
from program_management.ddd.domain.program_tree import ProgramTreeIdentity, ProgramTreeBuilder
from program_management.ddd.domain.report import Report, ReportIdentity
from program_management.ddd.domain.service import copy_tree_cms
from program_management.ddd.repositories import program_tree as tree_repository, node as node_repository


def fill_program_tree_content_from_last_year(cmd: 'FillProgramTreeContentFromLastYearCommand') -> 'ProgramTreeIdentity':
    tree_identity = ProgramTreeIdentity(code=cmd.to_code, year=cmd.to_year)
    last_year_tree_identity = ProgramTreeIdentity(code=cmd.to_code, year=cmd.to_year-1)
    repo = tree_repository.ProgramTreeRepository()
    node_repo = node_repository.NodeRepository()

    tree = repo.get(tree_identity)
    tree.report = Report(entity_id=ReportIdentity(transaction_id=cmd.transaction_id))
    last_year_tree = repo.get(last_year_tree_identity)

    existing_trees = repo.search(
        entity_ids=[
            ProgramTreeIdentity(code=node.code, year=cmd.to_year)
            for node in last_year_tree.root_node.get_all_children_as_nodes()
        ]
    )
    existing_learning_unit_nodes = node_repo.search(
        [
            attr.evolve(node.entity_id, year=cmd.to_year)
            for node in last_year_tree.root_node.get_all_children_as_learning_unit_nodes()
        ]
    )

    existing_nodes = [tree.root_node for tree in existing_trees] + existing_learning_unit_nodes

    ProgramTreeBuilder().fill_from_last_year_program_tree(last_year_tree, tree, set(existing_nodes))
    ProgramTreeBuilder().copy_prerequisites_from_program_tree(last_year_tree, tree)

    repo.create(tree, copy_group_service=copy_group_service.copy_group)

    copy_tree_cms.CopyCms().from_tree(last_year_tree, tree)

    return tree_identity
