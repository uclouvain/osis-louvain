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
from typing import List

import factory.fuzzy

from base.models.enums.prerequisite_operator import AND
from program_management.ddd.domain.prerequisite import Prerequisites
from program_management.ddd.domain.program_tree import ProgramTree
from program_management.tests.ddd.factories.prerequisite import PrerequisiteFactory, PrerequisiteItemGroupFactory, \
    PrerequisiteItemFactory


class PrerequisitesFactory(factory.Factory):

    class Meta:
        model = Prerequisites
        abstract = False

    context_tree = factory.SubFactory("..ProgramTreeIdentityFactory")
    prerequisites = factory.LazyFunction(list)

    @staticmethod
    def produce_inside_tree(
            context_tree: 'ProgramTree',
            node_having_prerequisite: 'NodeIdentity',
            nodes_that_are_prequisites: List['NodeIdentity'],
            operator=None
    ) -> None:
        if operator is None:
            operator = AND
        prerequisites = PrerequisitesFactory(
            context_tree=context_tree.entity_id,
            prerequisites=[
                PrerequisiteFactory(
                    node_having_prerequisites=node_having_prerequisite,
                    context_tree=context_tree.entity_id,
                    prerequisite_item_groups=[
                        PrerequisiteItemGroupFactory(
                            operator=operator,
                            prerequisite_items=[
                                PrerequisiteItemFactory(
                                    code=node_that_is_prequisite.code,
                                    year=node_that_is_prequisite.year
                                )
                                for node_that_is_prequisite in nodes_that_are_prequisites
                            ]
                        )
                    ]
                )
            ]
        )
        context_tree.prerequisites.prerequisites += prerequisites.prerequisites
