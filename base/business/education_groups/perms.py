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
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _, pgettext

from base.business.group_element_years.postponement import PostponeContent, NotPostponeError
from base.models.academic_calendar import AcademicCalendar
from base.models.education_group_type import find_authorized_types
from base.models.enums import academic_calendar_type
from base.models.enums.education_group_categories import TRAINING, MINI_TRAINING, GROUP

ERRORS_MSG = {
    "base.add_educationgroup": "The user has not permission to create education groups.",
    "base.change_educationgroup": "The user has not permission to change education groups.",
    "base.delete_educationgroup": "The user has not permission to delete education groups.",
}


def is_eligible_to_add_training(person, education_group, raise_exception=False):
    return _is_eligible_to_add_education_group(person, education_group, TRAINING, raise_exception)


def is_eligible_to_add_mini_training(person, education_group, raise_exception=False):
    return _is_eligible_to_add_education_group(person, education_group, MINI_TRAINING, raise_exception)


def is_eligible_to_add_group(person, education_group, raise_exception=False):
    return _is_eligible_to_add_education_group(person, education_group, GROUP, raise_exception)


def _is_eligible_to_add_education_group(person, education_group, category, raise_exception=False):
    return check_permission(person, "base.add_educationgroup", raise_exception) and \
           _is_eligible_to_add_education_group_with_category(person, category, raise_exception) and \
           _is_eligible_education_group(person, education_group, raise_exception) and \
           check_authorized_type(education_group, category, raise_exception)


def is_eligible_to_change_education_group(person, education_group, raise_exception=False):
    return check_permission(person, "base.change_educationgroup", raise_exception) and \
           _is_eligible_education_group(person, education_group, raise_exception)


def is_eligible_to_postpone_education_group(person, education_group, raise_exception=False):
    result = check_permission(person, "base.change_educationgroup", raise_exception) and \
             _is_eligible_education_group(person, education_group, raise_exception)

    try:
        # Check if the education group is valid
        PostponeContent(education_group.previous_year())
    except NotPostponeError as e:
        result = False
        if raise_exception:
            raise PermissionDenied(str(e))
    return result


def is_eligible_to_add_achievement(person, education_group, raise_exception=False):
    return check_permission(person, "base.add_educationgroupachievement", raise_exception) and \
           check_link_to_management_entity(education_group, person, raise_exception)


def is_eligible_to_change_achievement(person, education_group, raise_exception=False):
    return check_permission(person, "base.change_educationgroupachievement", raise_exception) and \
           check_link_to_management_entity(education_group, person, raise_exception)


def is_eligible_to_delete_achievement(person, education_group, raise_exception=False):
    return check_permission(person, "base.delete_educationgroupachievement", raise_exception) and \
           check_link_to_management_entity(education_group, person, raise_exception)


def is_eligible_to_delete_education_group(person, education_group, raise_exception=False):
    return check_permission(person, "base.delete_educationgroup", raise_exception) and \
           _is_eligible_education_group(person, education_group, raise_exception)


def is_academic_calendar_opened(education_group, type_academic_calendar, raise_exception=False):
    result = False

    ac = AcademicCalendar.objects.filter(reference=type_academic_calendar).open_calendars()

    # Check if the edition period is open
    if not ac:
        can_raise_exception(raise_exception, result, "The education group edition period is not open.")

    # During the edition period, the manager can only edit the N+1 education_group_year.
    elif education_group and education_group.academic_year != ac.get().academic_year.next():
        can_raise_exception(
            raise_exception, result, "this education group is not editable during this period."
        )

    else:
        result = True

    return result


def _is_eligible_education_group(person, education_group, raise_exception):
    return (check_link_to_management_entity(education_group, person, raise_exception) and
            (person.is_central_manager() or
             is_academic_calendar_opened(
                 education_group,
                 academic_calendar_type.EDUCATION_GROUP_EDITION,
                 raise_exception
             )
             )
            )


def _is_eligible_to_add_education_group_with_category(person, category, raise_exception):
    # TRAINING/MINI_TRAINING can only be added by central managers | Faculty manager must make a proposition of creation
    result = person.is_central_manager() or (person.is_faculty_manager() and category == GROUP)
    msg = _("The user has not permission to create a %(category)s.") % {"category": _(category)}
    can_raise_exception(raise_exception, result, msg)
    return result


def check_link_to_management_entity(education_group, person, raise_exception):
    if education_group:
        eligible_entities = get_education_group_year_eligible_management_entities(education_group)
        result = person.is_attached_entities(eligible_entities)
    else:
        result = True

    can_raise_exception(raise_exception, result, "The user is not attached to the management entity")

    return result


def check_permission(person, permission, raise_exception=False):
    result = person.user.has_perm(permission)
    can_raise_exception(raise_exception, result, ERRORS_MSG.get(permission, ""))

    return result


def can_raise_exception(raise_exception, result, msg):
    if raise_exception and not result:
        raise PermissionDenied(_(msg).capitalize())


def check_authorized_type(education_group, category, raise_exception=False):
    if not education_group or not category:
        return True

    result = find_authorized_types(
        category=category,
        parents=[education_group]
    ).exists()

    parent_category = education_group.education_group_type.category
    can_raise_exception(
        raise_exception, result,
        pgettext(
            "female" if parent_category in [TRAINING, MINI_TRAINING] else "male",
            "No type of %(child_category)s can be created as child of %(category)s of type %(type)s"
        ) % {
            "child_category": _(category),
            "category": _(education_group.education_group_type.category),
            "type": education_group.education_group_type.name,
        })

    return result


def get_education_group_year_eligible_management_entities(education_group):
    if education_group and education_group.management_entity:
        return [education_group.management_entity]

    eligible_entities = []
    for group in education_group.child_branch.all().select_related('parent'):
        eligible_entities += get_education_group_year_eligible_management_entities(group.parent)

    return eligible_entities


def is_eligible_to_edit_general_information(person, education_group, raise_exception=False):
    return check_permission(person, 'base.can_edit_educationgroup_pedagogy', raise_exception) and \
           _is_eligible_to_edit_general_information(person, education_group, raise_exception)


def _is_eligible_to_edit_general_information(person, education_group, raise_exception):
    return (education_group.is_common and person.is_sic()) or \
           check_link_to_management_entity(education_group, person, raise_exception) and \
           (
                   person.is_central_manager() or
                   is_academic_calendar_opened(
                        education_group,
                        academic_calendar_type.EDUCATION_GROUP_EDITION,
                        raise_exception
                   )
           )
