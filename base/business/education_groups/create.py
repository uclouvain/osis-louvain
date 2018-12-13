##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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

from base.business.utils import model
from base.forms.common import ValidationRuleMixin
from base.models.authorized_relationship import AuthorizedRelationship
from base.models.education_group import EducationGroup
from base.models.education_group_year import EducationGroupYear
from base.models.enums import count_constraint
from base.models.group_element_year import GroupElementYear
from base.models.utils import utils
from base.models.validation_rule import ValidationRule

REGEX_TRAINING_PARTIAL_ACRONYM = r"^(?P<sigle_ele>[A-Z]{3,5})\d{3}[A-Z]$"
REGEX_GROUP_PARTIAL_ACRONYM_INITIAL_VALUE = r"^(?P<cnum>\d{3})(?P<subdivision>[A-Z])$"
MAX_CNUM = 999
WIDTH_CNUM = 3


def create_initial_group_element_year_structure(parent_egys):
    children_created = defaultdict(list)
    if not parent_egys:
        return children_created

    first_parent = parent_egys[0]
    other_parents = parent_egys[1:]

    auth_rels = AuthorizedRelationship.objects.filter(
        parent_type=first_parent.education_group_type,
        min_count_authorized=count_constraint.ONE
    ).only('child_type').select_related('child_type')

    for relationship in auth_rels:
        child_education_group_type = relationship.child_type

        validation_rule_title = _get_validation_rule("title", child_education_group_type)
        validation_rule_partial_acronym = _get_validation_rule("partial_acronym", child_education_group_type)

        grp_ele = _get_or_create_branch(
            child_education_group_type,
            validation_rule_title.initial_value,
            validation_rule_partial_acronym.initial_value,
            first_parent
        )
        children_created[first_parent.id].append(grp_ele)
        for parent_egy in other_parents:
            grp_ele = _duplicate_branch(child_education_group_type, parent_egy, grp_ele.child_branch)
            children_created[parent_egy.id].append(grp_ele)
    return children_created


def _get_or_create_branch(child_education_group_type, title_initial_value, partial_acronym_initial_value, parent_egy):
    existing_grp_ele = utils.get_object_or_none(
        GroupElementYear,
        parent=parent_egy,
        child_branch__education_group_type=child_education_group_type
    )
    if existing_grp_ele:
        return existing_grp_ele

    year = parent_egy.academic_year.year
    child_eg = EducationGroup.objects.create(start_year=year, end_year=year)

    child_egy = EducationGroupYear.objects.create(
        academic_year=parent_egy.academic_year,
        main_teaching_campus=parent_egy.main_teaching_campus,
        management_entity=parent_egy.management_entity,
        education_group_type=child_education_group_type,
        title="{child_title} {parent_acronym}".format(
            child_title=title_initial_value,
            parent_acronym=parent_egy.acronym
        ),
        partial_acronym=_generate_child_partial_acronym(
            parent_egy,
            partial_acronym_initial_value,
            child_education_group_type
        ),
        acronym="{child_title}{parent_acronym}".format(
            child_title=title_initial_value.replace(" ", "").upper(),
            parent_acronym=parent_egy.acronym
        ),
        education_group=child_eg
    )

    grp_ele = GroupElementYear.objects.create(parent=parent_egy, child_branch=child_egy)
    return grp_ele


def _duplicate_branch(child_education_group_type, parent_egy, last_child):
    existing_grp_ele = utils.get_object_or_none(
        GroupElementYear,
        parent=parent_egy,
        child_branch__education_group_type=child_education_group_type
    )
    if existing_grp_ele:
        return existing_grp_ele

    year = parent_egy.academic_year.year
    child_eg = EducationGroup.objects.create(start_year=year, end_year=year)

    child_egy = model.duplicate_object(last_child)
    child_egy.education_group = child_eg
    child_egy.academic_year = parent_egy.academic_year
    child_egy.save()

    grp_ele = GroupElementYear.objects.create(parent=parent_egy, child_branch=child_egy)
    return grp_ele


def _get_validation_rule(field_name, education_group_type):
    egy_title_reference = ValidationRuleMixin._field_reference(
        EducationGroupYear,
        field_name,
        education_group_type.external_id
    )
    return ValidationRule.objects.get(pk=egy_title_reference)


def _generate_child_partial_acronym(parent, child_initial_value, child_type):
    previous_grp_ele = utils.get_object_or_none(
        GroupElementYear,
        parent__education_group=parent.education_group,
        parent__academic_year__year__in=[parent.academic_year.year - 1, parent.academic_year.year],
        child_branch__education_group_type=child_type
    )
    if previous_grp_ele:
        return previous_grp_ele.child_branch.partial_acronym

    reg_parent_partial_acronym = re.compile(REGEX_TRAINING_PARTIAL_ACRONYM)
    match_result = reg_parent_partial_acronym.search(parent.partial_acronym)
    sigle_ele = match_result.group("sigle_ele")

    reg_child_initial_value = re.compile(REGEX_GROUP_PARTIAL_ACRONYM_INITIAL_VALUE)
    match_result = reg_child_initial_value.search(child_initial_value)
    cnum, subdivision = match_result.group("cnum", "subdivision")

    partial_acronym = "{}{}{}".format(sigle_ele, cnum, subdivision)
    while EducationGroupYear.objects.filter(partial_acronym=partial_acronym).exists():
        cnum = "{:0{width}d}".format(
            (int(cnum) + 1) % MAX_CNUM,
            width=WIDTH_CNUM
        )
        partial_acronym = "{}{}{}".format(sigle_ele, cnum, subdivision)

    return partial_acronym
