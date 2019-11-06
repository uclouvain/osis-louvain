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
#############################################################################

from base.models import group_element_year as mdl_group_element_year
from base.models.learning_unit import LearningUnit


def extract_learning_units_acronym_from_prerequisite(prerequisite):
    learning_units = LearningUnit.objects.filter(prerequisiteitem__prerequisite=prerequisite)
    return [lu.acronym for lu in learning_units]


def get_learning_acronyms_inside_education_groups(education_group_years_id):
    if not education_group_years_id:
        return []
    geys = mdl_group_element_year.GroupElementYear.objects.filter(parent__in=education_group_years_id).\
        values("child_branch", "child_leaf__acronym")
    child_leafs_acronyms = [gey["child_leaf__acronym"] for gey in geys if gey["child_leaf__acronym"]]
    child_branches = [gey["child_branch"] for gey in geys if gey["child_branch"]]
    return child_leafs_acronyms + get_learning_acronyms_inside_education_groups(child_branches)


def get_learning_units_which_are_outside_of_education_group(education_group_year_root, list_learning_unit_acronyms):
    list_acronyms_inside_education_group = get_learning_acronyms_inside_education_groups([education_group_year_root.id])
    return list(set(list_learning_unit_acronyms) - set(list_acronyms_inside_education_group))


def get_prerequisite_acronyms_which_are_outside_of_education_group(education_group_year_root, prerequisite_obj):
    list_prerequisites_acronyms = extract_learning_units_acronym_from_prerequisite(prerequisite_obj)
    return get_learning_units_which_are_outside_of_education_group(education_group_year_root,
                                                                   list_prerequisites_acronyms)
