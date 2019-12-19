# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import gettext_lazy as _

from base.business.education_groups.perms import can_raise_exception, \
    is_eligible_to_change_education_group, check_permission
from base.business.event_perms import EventPermEducationGroupEdition
from base.models.enums.education_group_types import GroupType


# TODO: Extract permission logic from logic of education group because it's manipulating tree structure
def is_eligible_to_update_group_element_year(person, group_element_year, raise_exception):
    return is_eligible_to_change_education_group(person, group_element_year.parent, raise_exception) and \
           _is_eligible_to_change_group_element_year(person, group_element_year, raise_exception) and \
           (not group_element_year.child_branch
            or _can_user_update_education_group_year_child(person, group_element_year.child_branch, raise_exception))


# TODO: Extract permission logic from logic of education group because it's manipulating tree structure
def is_eligible_to_detach_group_element_year(person, group_element_year, raise_exception):
    return is_eligible_to_change_education_group(person, group_element_year.parent, raise_exception) and \
           _is_eligible_to_change_group_element_year(person, group_element_year, raise_exception)


def is_eligible_to_update_group_element_year_content(person, group_element_year, raise_exception):
    result = check_permission(person, "base.change_educationgroupcontent", raise_exception) and \
         is_eligible_to_update_group_element_year(person, group_element_year, raise_exception)
    can_raise_exception(raise_exception, result, _("The user is not allowed to change education group content."))
    return result


def _is_eligible_to_change_group_element_year(person, group_element_year, raise_exception):
    return person.is_central_manager or EventPermEducationGroupEdition(
        obj=group_element_year.parent,
        raise_exception=raise_exception
    ).is_open()


def _can_user_update_education_group_year_child(person, egy_child, raise_exception):
    group_type_only_central_can_update = (GroupType.MAJOR_LIST_CHOICE.name, GroupType.MINOR_LIST_CHOICE.name)
    result = person.is_central_manager or (
            egy_child.education_group_type.name not in group_type_only_central_can_update and not egy_child.is_minor
    )
    can_raise_exception(
        raise_exception,
        result,
        _("You cannot modify content for %(education_group_types)s") % {
            "education_group_types": ", ".join([str(GroupType.MAJOR_LIST_CHOICE.value),
                                                str(GroupType.MINOR_LIST_CHOICE.value)])
        })
    return result
