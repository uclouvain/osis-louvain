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
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _, pgettext

from base.business.group_element_years import management
from base.business.group_element_years.postponement import PostponeContent, NotPostponeError
from base.models.academic_calendar import AcademicCalendar
from base.models.academic_year import current_academic_year
from base.models.education_group_type import find_authorized_types
from base.models.enums import academic_calendar_type
from base.models.enums.education_group_categories import TRAINING, MINI_TRAINING, Categories

ERRORS_MSG = {
    "base.add_educationgroup": "The user has not permission to create education groups.",
    "base.change_educationgroup": "The user has not permission to change education groups.",
    "base.delete_educationgroup": "The user has not permission to delete education groups.",
}


def is_eligible_to_add_training(person, education_group, raise_exception=False):
    return _is_eligible_to_add_education_group(person, education_group, Categories.TRAINING,
                                               raise_exception=raise_exception)


def is_eligible_to_add_mini_training(person, education_group, raise_exception=False):
    return _is_eligible_to_add_education_group(person, education_group, Categories.MINI_TRAINING,
                                               raise_exception=raise_exception)


def is_eligible_to_add_group(person, education_group, raise_exception=False):
    return _is_eligible_to_add_education_group(person, education_group, Categories.GROUP,
                                               raise_exception=raise_exception)


def _is_eligible_to_add_education_group(person, education_group, category, education_group_type=None,
                                        raise_exception=False):
    return check_permission(person, "base.add_educationgroup", raise_exception) and \
           _is_eligible_to_add_education_group_with_category(person, category, raise_exception) and \
           _is_eligible_education_group(person, education_group, raise_exception) and \
           (not management.is_max_child_reached(education_group, education_group_type.name)
            if education_group_type and education_group
            else check_authorized_type(education_group, category, raise_exception))


def is_eligible_to_change_education_group(person, education_group, raise_exception=False):
    return check_permission(person, "base.change_educationgroup", raise_exception) and \
           _is_eligible_education_group(person, education_group, raise_exception)


def is_eligible_to_change_coorganization(person, education_group, raise_exception=False):
    return check_permission(person, "base.change_educationgroup", raise_exception) and \
           check_link_to_management_entity(education_group, person, raise_exception) and person.is_central_manager


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


def is_education_group_edit_period_opened(education_group, raise_exception=False):
    error_msg = None

    qs = AcademicCalendar.objects.filter(reference=academic_calendar_type.EDUCATION_GROUP_EDITION).open_calendars()
    if not qs.exists():
        error_msg = "The education group edition period is not open."
    elif education_group and not qs.filter(academic_year=education_group.academic_year).exists():
        error_msg = "This education group is not editable during this period."

    result = error_msg is None
    can_raise_exception(raise_exception, result, error_msg)
    return result


def _is_eligible_education_group(person, education_group, raise_exception):
    return (check_link_to_management_entity(education_group, person, raise_exception) and
            (person.is_central_manager or is_education_group_edit_period_opened(education_group, raise_exception)))


def _is_eligible_to_add_education_group_with_category(person, category, raise_exception):
    # TRAINING/MINI_TRAINING can only be added by central managers | Faculty manager must make a proposition of creation
    # based on US OSIS-2592, Faculty manager can add a MINI-TRAINING
    result = person.is_central_manager or (person.is_faculty_manager and category == Categories.MINI_TRAINING)

    msg = pgettext(
        "male" if category == Categories.GROUP else "female",
        "The user has not permission to create a %(category)s."
    ) % {"category": category.value}

    can_raise_exception(raise_exception, result, msg)
    return result


def check_link_to_management_entity(education_group, person, raise_exception):
    if education_group:
        eligible_entities = get_education_group_year_eligible_management_entities(education_group)
        result = person.is_attached_entities(eligible_entities)
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


def check_authorized_type(education_group, category, raise_exception=False):
    if not education_group or not category:
        return True

    result = find_authorized_types(
        category=category.name,
        parents=[education_group]
    ).exists()

    parent_category = education_group.education_group_type.category
    can_raise_exception(
        raise_exception, result,
        pgettext(
            "female" if parent_category in [TRAINING, MINI_TRAINING] else "male",
            "No type of %(child_category)s can be created as child of %(category)s of type %(type)s"
        ) % {
            "child_category": category.value,
            "category": education_group.education_group_type.get_category_display(),
            "type": education_group.education_group_type.get_name_display(),
        })

    return result


def get_education_group_year_eligible_management_entities(education_group):
    if education_group and education_group.management_entity:
        return [education_group.management_entity]

    eligible_entities = []
    for group in education_group.child_branch.all().select_related('parent'):
        eligible_entities += get_education_group_year_eligible_management_entities(group.parent)

    return eligible_entities


def is_eligible_to_edit_general_information(person, education_group_year, raise_exception=False):
    perm = GeneralInformationPerms(person.user, education_group_year)
    return perm.is_eligible(raise_exception)


def is_eligible_to_edit_admission_condition(person, education_group_year, raise_exception=False):
    perm = AdmissionConditionPerms(person.user, education_group_year)
    return perm.is_eligible(raise_exception)


class CommonEducationGroupStrategyPerms(object):
    def __init__(self, user, education_group_year):
        self.user = user
        self.education_group_year = education_group_year
        super().__init__()

    @cached_property
    def person(self):
        return self.user.person

    def is_eligible(self, raise_exception=False):
        try:
            return self._is_eligible()
        except PermissionDenied:
            if not raise_exception:
                return False
            raise

    def _is_eligible(self):
        if self.user.is_superuser:
            return True

        if not self._is_current_academic_year_in_range_of_editable_education_group_year():
            raise PermissionDenied(_("The user cannot modify data which are greater than N+1"))
        if not self._is_linked_to_management_entity():
            raise PermissionDenied(_("The user is not attached to the management entity"))
        return True

    def _is_current_academic_year_in_range_of_editable_education_group_year(self):
        return self.education_group_year.academic_year.year < current_academic_year().year + 2

    def _is_linked_to_management_entity(self):
        return check_link_to_management_entity(self.education_group_year, self.person, False)


class GeneralInformationPerms(CommonEducationGroupStrategyPerms):
    def _is_eligible(self):
        super()._is_eligible()

        if not self._is_user_have_perm():
            raise PermissionDenied(_("The user doesn't have right to update general information"))

        if self.person.is_central_manager:
            return self._is_central_manager_eligible()
        elif self.person.is_faculty_manager:
            return self._is_faculty_manager_eligible()
        elif self.person.is_sic:
            return self._is_sic_eligible()
        return False

    def _is_user_have_perm(self):
        perm_name = 'base.change_commonpedagogyinformation' if self.education_group_year.is_common else \
            'base.change_pedagogyinformation'
        return check_permission(self.person, perm_name, False)

    def _is_central_manager_eligible(self):
        return True

    def _is_faculty_manager_eligible(self):
        if self.education_group_year.academic_year.year < current_academic_year().year:
            raise PermissionDenied(_("The faculty manager cannot modify general information which are lower than N"))
        return True

    def _is_sic_eligible(self):
        return True


class AdmissionConditionPerms(CommonEducationGroupStrategyPerms):
    def _is_eligible(self):
        super()._is_eligible()

        if not self._is_user_have_perm():
            raise PermissionDenied(_("The user doesn't have right to update admission condition"))

        if self.person.is_central_manager:
            return self._is_central_manager_eligible()
        elif self.person.is_faculty_manager:
            return self._is_faculty_manager_eligible()
        elif self.person.is_sic:
            return self._is_sic_eligible()
        return False

    def _is_user_have_perm(self):
        perm_name = 'base.change_commonadmissioncondition' if self.education_group_year.is_common else \
            'base.change_admissioncondition'
        return check_permission(self.person, perm_name, False)

    def _is_central_manager_eligible(self):
        return True

    def _is_faculty_manager_eligible(self):
        if self.education_group_year.academic_year.year < current_academic_year().year:
            raise PermissionDenied(_("The faculty manager cannot modify admission which are lower than N"))
        if not is_education_group_edit_period_opened(self.education_group_year):
            raise PermissionDenied(_("The faculty manager cannot modify outside of program edition period"))
        return True

    def _is_sic_eligible(self):
        return True
