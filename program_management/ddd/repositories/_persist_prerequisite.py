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
from django.db import transaction

from base.models import education_group_year, learning_unit_year, prerequisite_item, learning_unit
from base.models import prerequisite as prerequisite_model
from program_management.ddd.domain import prerequisite as prerequisite_domain, program_tree
from program_management.ddd.domain.node import NodeLearningUnitYear, NodeEducationGroupYear
from program_management.models.enums.node_type import NodeType


def persist(tree: program_tree.ProgramTree):
    all_learning_unit_nodes = tree.get_nodes_by_type(NodeType.LEARNING_UNIT)
    learning_unit_nodes_modified = [node for node in all_learning_unit_nodes if node.prerequisite.has_changed]
    for node in learning_unit_nodes_modified:
        _persist(tree.root_node, node)


def _persist(
        node_education_group_year: NodeEducationGroupYear,
        node_learning_unit_year_obj: NodeLearningUnitYear,
) -> None:
    education_group_year_obj = education_group_year.EducationGroupYear.objects.get(
        id=node_education_group_year.node_id
    )
    learning_unit_year_obj = learning_unit_year.LearningUnitYear.objects.get(
        id=node_learning_unit_year_obj.node_id
    )
    prerequisite = node_learning_unit_year_obj.prerequisite

    prerequisite_model_obj, created = prerequisite_model.Prerequisite.objects.update_or_create(
        education_group_year=education_group_year_obj,
        learning_unit_year=learning_unit_year_obj,
        defaults={"main_operator": prerequisite.main_operator}
    )
    _delete_prerequisite_items(prerequisite_model_obj)
    _persist_prerequisite_items(prerequisite_model_obj, prerequisite)


def _delete_prerequisite_items(prerequisite_model_obj: prerequisite_model.Prerequisite):
    items = prerequisite_model_obj.prerequisiteitem_set.all()
    for item in items:
        item.delete()


def _persist_prerequisite_items(
        prerequisite_model_obj: prerequisite_model.Prerequisite,
        prerequisite_domain_obj: prerequisite_domain.Prerequisite
):
    for group_number, group in enumerate(prerequisite_domain_obj.prerequisite_item_groups, 1):
        for position, item in enumerate(group.prerequisite_items, 1):

            learning_unit_obj = _get_learning_unit_of_prerequisite_item(item)

            prerequisite_item.PrerequisiteItem.objects.create(
                prerequisite=prerequisite_model_obj,
                learning_unit=learning_unit_obj,
                group_number=group_number,
                position=position,
            )


def _get_learning_unit_of_prerequisite_item(prerequisite_item_domain_obj: prerequisite_domain.PrerequisiteItem):
    return learning_unit.LearningUnit.objects.filter(
        learningunityear__acronym=prerequisite_item_domain_obj.code,
        learningunityear__academic_year__year=prerequisite_item_domain_obj.year
    ).first()
