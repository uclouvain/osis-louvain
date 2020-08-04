##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
import re
from collections import defaultdict
from typing import List, Dict, Pattern, Tuple

from django.db.models import Case, When, Value, IntegerField

from base.business.utils import model
from base.forms.common import ValidationRuleMixin
from base.models.authorized_relationship import AuthorizedRelationship
from base.models.education_group import EducationGroup
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import GroupType
from base.models.group_element_year import GroupElementYear
from base.models.validation_rule import ValidationRule
from osis_common.utils.models import get_object_or_none

REGEX_TRAINING_PARTIAL_ACRONYM = r"^(?P<sigle_ele>[A-Z]{3,5})\d{3}[A-Z]$"
REGEX_COMMON_PARTIAL_ACRONYM = r"^(?P<sigle_ele>common(-\d[a-z]{1,2})?)$"
REGEX_GROUP_PARTIAL_ACRONYM_INITIAL_VALUE = r"^(?P<cnum>\d{3})(?P<subdivision>[A-Z])$"
MAX_CNUM = 999
WIDTH_CNUM = 3


#  FIXME :: To remove - implemented in TrainingBuilder
def create_initial_group_element_year_structure(
        parent_egys: List[EducationGroupYear]) -> Dict[int, List[GroupElementYear]]:
    children_created = defaultdict(list)
    if not parent_egys:
        return children_created

    first_parent = parent_egys[0]
    other_parents = parent_egys[1:]

    auth_rels = AuthorizedRelationship.objects.filter(
        parent_type=first_parent.education_group_type,
        min_count_authorized=1
    ).annotate(
        rels_ordering=Case(
            *[When(child_type__name=type_name, then=Value(i)) for i, type_name in enumerate(GroupType.ordered())],
            default=Value(len(GroupType.ordered())),
            output_field=IntegerField()
        )
    ).order_by(
        "rels_ordering"
    ).only('child_type').select_related('child_type')

    for relationship in auth_rels:
        child_education_group_type = relationship.child_type

        validation_rule_title = _get_validation_rule("title", child_education_group_type)
        validation_rule_partial_acronym = _get_validation_rule("partial_acronym", child_education_group_type)

        grp_ele = _get_or_create_branch(
            child_education_group_type,
            validation_rule_title.initial_value if validation_rule_title else "",
            validation_rule_partial_acronym.initial_value if validation_rule_partial_acronym else "",
            first_parent
        )
        children_created[first_parent.id].append(grp_ele)
        for parent_egy in other_parents:
            grp_ele = _duplicate_branch(child_education_group_type, parent_egy, grp_ele.child_branch)
            children_created[parent_egy.id].append(grp_ele)
    return children_created


def _get_or_create_branch(
        child_education_group_type: str,
        title_initial_value: str,
        partial_acronym_initial_value: str,
        parent_egy: EducationGroupYear) -> GroupElementYear:
    existing_grp_ele = get_object_or_none(
        GroupElementYear,
        parent=parent_egy,
        child_branch__education_group_type=child_education_group_type
    )
    if existing_grp_ele:
        return existing_grp_ele

    academic_year = parent_egy.academic_year
    previous_grp_ele = get_object_or_none(
        GroupElementYear,
        parent__education_group=parent_egy.education_group,
        parent__academic_year__year__in=[academic_year.year - 1, academic_year.year],
        child_branch__education_group_type=child_education_group_type
    )
    edy_acronym = "{child_title}{parent_acronym}".format(
        child_title=title_initial_value.replace(" ", "").upper(),
        parent_acronym=parent_egy.acronym
    )[:EducationGroupYear._meta.get_field("acronym").max_length]

    if not previous_grp_ele:
        ed = EducationGroup.objects.filter(
            educationgroupyear__acronym=edy_acronym,
        )
        if ed.exists():
            child_eg = ed.first()
        else:
            child_eg = EducationGroup.objects.create(start_year=academic_year, end_year=academic_year)
    else:
        edy_acronym = previous_grp_ele.child_branch.acronym
        child_eg = previous_grp_ele.child_branch.education_group

    child_egy, _ = EducationGroupYear.objects.update_or_create(
        academic_year=parent_egy.academic_year,
        education_group=child_eg,
        defaults={
            'main_teaching_campus': parent_egy.main_teaching_campus,
            'management_entity': parent_egy.management_entity,
            'education_group_type': child_education_group_type,
            'title': "{child_title} {parent_acronym}".format(
                child_title=title_initial_value,
                parent_acronym=parent_egy.acronym
            ),
            'partial_acronym': _generate_child_partial_acronym(
                parent_egy,
                partial_acronym_initial_value,
                child_education_group_type
            ),
            'acronym': edy_acronym,
        }
    )
    gey, _ = GroupElementYear.objects.get_or_create(parent=parent_egy, child_branch=child_egy)
    return gey


def _duplicate_branch(
        child_education_group_type: str,
        parent_egy: EducationGroupYear,
        last_child: EducationGroupYear) -> GroupElementYear:
    existing_grp_ele = get_object_or_none(
        GroupElementYear,
        parent=parent_egy,
        child_branch__education_group_type=child_education_group_type
    )
    if existing_grp_ele:
        return existing_grp_ele

    academic_year = parent_egy.academic_year
    last_child.education_group.end_year = academic_year
    last_child.education_group.save()

    child_egy = model.duplicate_object(last_child)
    child_egy.education_group = last_child.education_group
    child_egy.academic_year = parent_egy.academic_year
    child_egy.save()

    return GroupElementYear.objects.create(parent=parent_egy, child_branch=child_egy)


def _get_validation_rule(
        field_name: str,
        education_group_type: str) -> ValidationRule:
    egy_title_reference = ValidationRuleMixin._field_reference(
        EducationGroupYear,
        field_name,
        education_group_type.external_id
    )
    return get_object_or_none(ValidationRule, pk=egy_title_reference)


#  FIXME :: To remove - implemented in generate_node_code.py
def _generate_child_partial_acronym(
        parent: EducationGroupYear,
        child_initial_value: str,
        child_type: str) -> str:
    previous_grp_ele = get_object_or_none(
        GroupElementYear,
        parent__education_group=parent.education_group,
        parent__academic_year__year__in=[parent.academic_year.year - 1, parent.academic_year.year],
        child_branch__education_group_type=child_type
    )
    if previous_grp_ele:
        return previous_grp_ele.child_branch.partial_acronym

    reg_parent_partial_acronym = re.compile(REGEX_TRAINING_PARTIAL_ACRONYM)
    reg_common_partial_acronym = re.compile(REGEX_COMMON_PARTIAL_ACRONYM)
    # FIXME : Sometimes parent does not have a partial acronym, it is a dirty situation. We have to clean the DB.
    if not parent.partial_acronym:
        return ""
    match_result = reg_parent_partial_acronym.search(parent.partial_acronym) or \
        reg_common_partial_acronym.search(parent.partial_acronym)
    sigle_ele = match_result.group("sigle_ele")

    reg_child_initial_value = re.compile(REGEX_GROUP_PARTIAL_ACRONYM_INITIAL_VALUE)
    cnum, subdivision = _get_cnum_subdivision(child_initial_value, reg_child_initial_value)

    partial_acronym = "{}{}{}".format(sigle_ele, cnum, subdivision)
    while EducationGroupYear.objects.filter(partial_acronym=partial_acronym).exists():
        cnum = "{:0{width}d}".format(
            (int(cnum) + 1) % MAX_CNUM,
            width=WIDTH_CNUM
        )
        partial_acronym = "{}{}{}".format(sigle_ele, cnum, subdivision)

    return partial_acronym


#  FIXME :: To remove - implemented in generate_node_code.py
def _get_cnum_subdivision(
        child_initial_value: str,
        reg_child_initial_value: Pattern) -> Tuple[str, str]:
    match_result = reg_child_initial_value.search(child_initial_value)
    if match_result:
        cnum, subdivision = match_result.group("cnum", "subdivision")
    else:
        cnum = None
        subdivision = None
    return cnum, subdivision
