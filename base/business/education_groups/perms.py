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
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from base.business.event_perms import EventPermEducationGroupEdition
from base.models.education_group_year import EducationGroupYear

ERRORS_MSG = {
    "base.add_educationgroup": _("The user does not have permission to create education groups."),
    "base.change_educationgroup": _("The user does not have permission to change education groups."),
    "base.delete_educationgroup": _("The user does not have permission to delete education groups."),
    "base.change_educationgroupcontent": _("The user is not allowed to change education group content.")
}


def is_eligible_to_change_education_group(person, education_group, raise_exception=False):
    return check_permission(person, "base.change_educationgroup", raise_exception) and \
           _is_eligible_education_group(person, education_group, raise_exception) and \
           _is_year_editable(education_group, raise_exception)


def is_eligible_to_change_education_group_content(person, education_group, raise_exception=False):
    return check_permission(person, "base.change_educationgroupcontent", raise_exception) and \
        is_eligible_to_change_education_group(person, education_group, raise_exception)


# FIXME :: DEPRECATED - Use MinimumEditableYearValidator
def _is_year_editable(education_group, raise_exception):
    error_msg = None
    if education_group.academic_year.year < settings.YEAR_LIMIT_EDG_MODIFICATION:
        error_msg = _("You cannot change a education group before %(limit_year)s") % {
            "limit_year": settings.YEAR_LIMIT_EDG_MODIFICATION}

    result = error_msg is None
    can_raise_exception(raise_exception, result, error_msg)
    return result


def _is_eligible_education_group(person, education_group, raise_exception):
    return (
        check_link_to_management_entity(education_group, person, raise_exception) and
        (
            person.is_central_manager or
            EventPermEducationGroupEdition(obj=education_group, raise_exception=raise_exception).is_open()
        )
    )


def check_link_to_management_entity(education_group, person, raise_exception):
    if education_group:
        if not hasattr(education_group, 'eligible_entities'):
            education_group.eligible_entities = get_education_group_year_eligible_management_entities(education_group)

        result = person.is_attached_entities(education_group.eligible_entities)
    else:
        result = True

    can_raise_exception(raise_exception, result, _("The user is not attached to the management entity"))

    return result


def check_permission(person, permission, raise_exception=False):
    result = person.user.has_perm(permission)
    can_raise_exception(raise_exception, result, ERRORS_MSG.get(permission, ""))
    return result


def can_raise_exception(raise_exception, result, msg):
    if raise_exception and not result:
        raise PermissionDenied(_(msg).capitalize())


def get_education_group_year_eligible_management_entities(education_group: EducationGroupYear):
    if education_group and education_group.management_entity:
        return [education_group.management_entity]

    eligible_entities = []
    for group in education_group.child_branch.all().select_related('parent'):
        eligible_entities += get_education_group_year_eligible_management_entities(group.parent)

    return eligible_entities
