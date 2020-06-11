##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from collections import Counter
from typing import List, Union, Tuple

from django.db.models import Count, Q
from django.utils.functional import cached_property
from django.utils.translation import gettext as _

from base.models.authorized_relationship import AuthorizedRelationship
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import AllTypes
from base.models.enums.link_type import LinkTypes
from base.models.group_element_year import GroupElementYear
from base.models.learning_unit_year import LearningUnitYear
from base.utils.cache import ElementCache
from program_management.ddd.domain import node
from program_management.ddd.repositories import load_node
from program_management.models.enums.node_type import NodeType

# FIXME Replace those methods by services
LEARNING_UNIT_YEAR = LearningUnitYear._meta.db_table
EDUCATION_GROUP_YEAR = EducationGroupYear._meta.db_table


def fetch_source_link(request_parameters, user):
    selected_data = _get_elements_selected(request_parameters, user)

    source_link = None
    for selected_element in selected_data:
        if selected_element.get('source_link_id'):
            source_link = GroupElementYear.objects.select_related('parent').get(pk=selected_element['source_link_id'])

    return source_link


# FIXME Migrate this method into ddd/service
def fetch_nodes_selected(request_parameters, user) -> List[Tuple[int, NodeType]]:
    def _convert_element_to_node_id_and_node_type(element) -> Tuple[int, NodeType]:
        if element['modelname'] == LEARNING_UNIT_YEAR:
            return element["id"], NodeType.LEARNING_UNIT
        return element["id"], NodeType.EDUCATION_GROUP

    selected_data = _get_elements_selected(request_parameters, user)
    return [_convert_element_to_node_id_and_node_type(element) for element in selected_data]


# FIXME :: DEPRECATED - Use AuthorizedRelationshipValidator from ddd instead
def fetch_elements_selected(request_parameters, user):
    selected_data = _get_elements_selected(request_parameters, user)

    children = []
    for selected_element in selected_data:
        if selected_element['modelname'] == LEARNING_UNIT_YEAR:
            children.append(LearningUnitYear.objects.get(pk=selected_element['id']))
        elif selected_element['modelname'] == EDUCATION_GROUP_YEAR:
            children.append(EducationGroupYear.objects.get(pk=selected_element['id']))

    return children


def _get_elements_selected(request_parameters, user):
    object_ids = request_parameters.getlist("id", [])
    content_type = request_parameters.get("content_type")
    if object_ids and content_type:
        selected_data = [{"id": object_id, "modelname": content_type} for object_id in object_ids]
    elif object_ids or content_type:
        selected_data = []
    else:
        cached_data = ElementCache(user).cached_data
        selected_data = [cached_data] if cached_data else []
    return selected_data


# FIXME :: DEPRECATED - Use AuthorizedRelationshipValidator from ddd instead
def is_max_child_reached(parent, child_education_group_type):
    try:
        auth_rel = parent.education_group_type.authorized_parent_type.get(child_type__name=child_education_group_type)
    except AuthorizedRelationship.DoesNotExist:
        return True

    try:
        education_group_type_count = _compute_number_children_by_education_group_type(parent, None). \
            get(education_group_type__name=child_education_group_type)["count"]
    except EducationGroupYear.DoesNotExist:
        education_group_type_count = 0
    return auth_rel.max_count_authorized is not None and education_group_type_count >= auth_rel.max_count_authorized


def _compute_number_children_by_education_group_type(root, link=None, to_delete=False):
    child_branch_id = None if not link else link.child_branch.id

    direct_children = (Q(child_branch__parent=root) &
                       Q(child_branch__link_type=None) &
                       ~Q(child_branch__id=child_branch_id))
    referenced_children = (Q(child_branch__parent__child_branch__parent=root) &
                           Q(child_branch__parent__child_branch__link_type=LinkTypes.REFERENCE.name) &
                           ~Q(child_branch__parent__id=child_branch_id))
    filter_children_clause = direct_children | referenced_children

    if link and not to_delete:
        link_children = Q(id=link.child_branch.id)
        if link.link_type == LinkTypes.REFERENCE.name:
            link_children = Q(child_branch__parent__id=link.child_branch.id)

        filter_children_clause = filter_children_clause | link_children

    return EducationGroupYear.objects.filter(
        filter_children_clause
    ).values(
        "education_group_type__name"
    ).order_by(
        "education_group_type__name"
    ).annotate(
        count=Count("education_group_type__name")
    )


# FIXME :: DEPRECATED - Use AuthorizedRelationshipValidator from ddd instead
class CheckAuthorizedRelationship:
    def __init__(self, parent, link_to_attach=None, link_to_detach=None):
        self.parent = parent
        self.link_to_attach = link_to_attach
        self.link_to_detach = link_to_detach

        self.min_reached_errors, self.max_reached_errors, self.not_authorized_errors = [], [], []

    @property
    def errors(self):
        return self.min_reached_errors + self.max_reached_errors + self.not_authorized_errors

    def is_valid(self):
        self._check_authorized_relationship()
        return len(self.errors) == 0

    def _check_authorized_relationship(self):
        children_type_count_after_attach_and_detach = self._children_type_count.copy()
        children_type_count_after_attach_and_detach.subtract(self._detach_link_children_type_count)
        children_type_count_after_attach_and_detach.update(self._attach_link_children_type_count)
        if self.link_to_attach and self.link_to_attach.pk and not self.link_to_attach.link_type:
            # We should avoid to count the elem that we are updating (pk exist on link_to_attach)
            children_type_count_after_attach_and_detach.subtract({
                self.link_to_attach.child_branch.education_group_type.name: 1
            })
        children_type_count_impacted = Counter(
            dict(
                (key, count) for key, count in children_type_count_after_attach_and_detach.items()
                if key in self._attach_link_children_type_count or key in self._detach_link_children_type_count
            )
        )
        min_reached_types = _filter_min_reached(children_type_count_impacted, self._authorized_relationships)
        not_authorized_types = _filter_not_authorized(children_type_count_impacted, self._authorized_relationships)
        max_reached_types = _filter_max_reached(children_type_count_impacted, self._authorized_relationships)

        if min_reached_types:
            self.min_reached_errors.append(_("The parent must have at least one child of type(s) \"%(types)s\".") % {
                "types": ', '.join(str(AllTypes.get_value(name)) for name in min_reached_types)
            })

        if max_reached_types:
            self.max_reached_errors.append(_("The number of children of type(s) \"%(child_types)s\" for \"%(parent)s\" "
                                             "has already reached the limit.") % {
                'child_types': ', '.join(str(AllTypes.get_value(name)) for name in max_reached_types),
                'parent': self.parent
            })
        if not_authorized_types:
            self.not_authorized_errors.append(_("You cannot add \"%(child_types)s\" to \"%(parent)s\" "
                                                "(type \"%(parent_type)s\")") % {
                'child_types': ', '.join(str(AllTypes.get_value(name)) for name in not_authorized_types),
                'parent': self.parent,
                'parent_type': AllTypes.get_value(self.parent.education_group_type.name),
            })

    @cached_property
    def _authorized_relationships(self):
        auth_rels_qs = self.parent.education_group_type.authorized_parent_type.all().select_related("child_type")
        return {auth_rel.child_type.name: auth_rel for auth_rel in auth_rels_qs}

    @cached_property
    def _children_type_count(self):
        direct_children = (Q(child_branch__parent=self.parent) & Q(child_branch__link_type=None))
        referenced_children = (Q(child_branch__parent__child_branch__parent=self.parent) &
                               Q(child_branch__parent__child_branch__link_type=LinkTypes.REFERENCE.name))
        # Use two queries because when using or clause on filter it returns duplicate data
        direct_children_type_count_qs = EducationGroupYear.objects.filter(
            direct_children
        ).values(
            "education_group_type__name"
        ).order_by(
            "education_group_type__name"
        ).annotate(
            count=Count("education_group_type__name")
        ).values_list("education_group_type__name", "count")

        referenced_children_type_count_qs = EducationGroupYear.objects.filter(
            referenced_children
        ).values(
            "education_group_type__name"
        ).order_by(
            "education_group_type__name"
        ).annotate(
            count=Count("education_group_type__name")
        ).values_list("education_group_type__name", "count")

        return Counter(dict(direct_children_type_count_qs)) + Counter(dict(referenced_children_type_count_qs))

    @cached_property
    def _attach_link_children_type_count(self):
        return self._link_children_type_count(self.link_to_attach) if self.link_to_attach else Counter()

    @cached_property
    def _detach_link_children_type_count(self):
        return self._link_children_type_count(self.link_to_detach) if self.link_to_detach else Counter()

    def _link_children_type_count(self, link):
        filter_children_clause = Q(id=link.child_branch.id)
        if link.link_type == LinkTypes.REFERENCE.name:
            filter_children_clause = Q(child_branch__parent__id=link.child_branch.id)

        children_type_count_qs = EducationGroupYear.objects.filter(
            filter_children_clause
        ).values(
            "education_group_type__name"
        ).order_by(
            "education_group_type__name"
        ).annotate(
            count=Count("education_group_type__name")
        ).values_list("education_group_type__name", "count")

        return Counter(dict(children_type_count_qs))


# FIXME :: DEPRECATED - Use AuthorizedRelationshipValidator from ddd instead
class CheckAuthorizedRelationshipAttach(CheckAuthorizedRelationship):
    @property
    def errors(self):
        return self.max_reached_errors + self.not_authorized_errors


# FIXME :: DEPRECATED - Use AuthorizedRelationshipValidator from ddd instead
class CheckAuthorizedRelationshipDetach(CheckAuthorizedRelationship):
    @property
    def errors(self):
        return self.min_reached_errors


def _filter_not_authorized(egy_type_count, auth_rels):
    return [egy_type for egy_type, count in egy_type_count.items() if egy_type not in auth_rels and count > 0]


def _filter_min_reached(egy_type_count, auth_rels):
    return [egy_type for egy_type, count in egy_type_count.items()
            if egy_type in auth_rels and count < auth_rels[egy_type].min_count_authorized]


def _filter_max_reached(egy_type_count, auth_rels):
    return [egy_type for egy_type, count in egy_type_count.items()
            if egy_type in auth_rels and auth_rels[egy_type].max_count_authorized is not None and
            count > auth_rels[egy_type].max_count_authorized]
