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
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q
from django.utils.translation import ugettext as _

from base.models.authorized_relationship import AuthorizedRelationship
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import AllTypes
from base.models.enums.link_type import LinkTypes
from base.models.exceptions import AuthorizedRelationshipNotRespectedException
from base.models.group_element_year import GroupElementYear
from base.models.learning_unit_year import LearningUnitYear
from base.utils.cache import ElementCache

LEARNING_UNIT_YEAR = LearningUnitYear._meta.db_table
EDUCATION_GROUP_YEAR = EducationGroupYear._meta.db_table


def extract_child_from_cache(parent, user):
    selected_data = ElementCache(user).cached_data
    if not selected_data:
        raise ObjectDoesNotExist

    kwargs = {'parent': parent}
    if selected_data['modelname'] == LEARNING_UNIT_YEAR:
        kwargs['child_leaf'] = LearningUnitYear.objects.get(pk=selected_data['id'])

    elif selected_data['modelname'] == EDUCATION_GROUP_YEAR:
        kwargs['child_branch'] = EducationGroupYear.objects.get(pk=selected_data['id'])

    if selected_data.get('source_link_id'):
        kwargs['source_link'] = GroupElementYear.objects.select_related('parent') \
            .get(pk=selected_data['source_link_id'])

    return kwargs


def is_max_child_reached(parent, child_education_group_type):
    try:
        auth_rel = parent.education_group_type.authorized_parent_type.get(child_type__name=child_education_group_type)
    except AuthorizedRelationship.DoesNotExist:
        return True

    try:
        education_group_type_count = compute_number_children_by_education_group_type(parent, None). \
            get(education_group_type__name=child_education_group_type)["count"]
    except EducationGroupYear.DoesNotExist:
        education_group_type_count = 0
    return auth_rel.max_count_authorized is not None and education_group_type_count >= auth_rel.max_count_authorized


def _check_authorized_relationship(root, link, to_delete=False):
    auth_rels = root.education_group_type.authorized_parent_type.all().select_related("child_type")
    auth_rels_dict = {auth_rel.child_type.name: auth_rel for auth_rel in auth_rels}

    count_children_by_education_group_type_qs = compute_number_children_by_education_group_type(root, link, to_delete)
    count_children_dict = {
        record["education_group_type__name"]: record["count"] for record in count_children_by_education_group_type_qs
    }

    max_reached, min_reached, not_authorized = [], [], []
    for key, count in count_children_dict.items():
        if to_delete:
            count -= 1

        if key not in auth_rels_dict:
            not_authorized.append(key)
        elif count < auth_rels_dict[key].min_count_authorized:
            min_reached.append(key)
        elif auth_rels_dict[key].max_count_authorized is not None and count > auth_rels_dict[key].max_count_authorized:
            max_reached.append(key)

    _min_reach_technical_group(auth_rels_dict, count_children_dict, min_reached)
    return min_reached, max_reached, not_authorized


def _min_reach_technical_group(auth_rels_dict, count_children_dict, min_reached):
    """ Check for technical group that would not be linked to root """
    for key, auth_rel in auth_rels_dict.items():
        if key not in count_children_dict and auth_rel.min_count_authorized > 0:
            min_reached.append(key)


def can_link_be_detached(root, link):
    min_reached, max_reached, not_authorized = _check_authorized_relationship(root, link, to_delete=True)
    if link.child_branch.education_group_type.name in min_reached:
        raise AuthorizedRelationshipNotRespectedException(
            message=_("The parent must have at least one child of type(s) \"%(types)s\".") % {
                "types": ', '.join(str(AllTypes.get_value(name)) for name in min_reached)
            }
        )


def check_authorized_relationship(root, link, to_delete=False):
    min_reached, max_reached, not_authorized = _check_authorized_relationship(root, link, to_delete=to_delete)

    if link.child_branch.education_group_type.name in min_reached:
        raise AuthorizedRelationshipNotRespectedException(
            errors=_("The parent must have at least one child of type(s) \"%(types)s\".") % {
                "types": ', '.join(str(AllTypes.get_value(name)) for name in min_reached)
            }
        )
    elif link.child_branch.education_group_type.name in max_reached:
        raise AuthorizedRelationshipNotRespectedException(
            errors=_("The number of children of type(s) \"%(child_types)s\" for \"%(parent)s\" "
                     "has already reached the limit.") % {
                       'child_types': ', '.join(str(AllTypes.get_value(name)) for name in max_reached),
                       'parent': root
                   }
        )
    elif link.child_branch.education_group_type.name in not_authorized:
        raise AuthorizedRelationshipNotRespectedException(
            errors=_("You cannot attach \"%(child_types)s\" to \"%(parent)s\" (type \"%(parent_type)s\")") % {
                'child_types': ', '.join(str(AllTypes.get_value(name)) for name in not_authorized),
                'parent': root,
                'parent_type': AllTypes.get_value(root.education_group_type.name),
            }
        )


def compute_number_children_by_education_group_type(root, link=None, to_delete=False):
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
