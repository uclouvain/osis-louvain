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
import datetime

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _

from attribution.business.perms import _is_tutor_attributed_to_the_learning_unit
from base.business.institution import find_summary_course_submission_dates_for_entity_version
from base.models import tutor, entity_calendar
from base.models.entity_version import EntityVersion
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.models.learning_unit_year import LearningUnitYear
from osis_common.utils.datetime import get_tzinfo, convert_date_to_datetime
from osis_common.utils.perms import BasePerm


# TODO : migrate with tutor role creation
def is_eligible_to_update_learning_unit_pedagogy(learning_unit_year, person):
    """
    Permission to edit learning unit pedagogy needs many conditions:
        - The person must have the permission can_edit_learning_pedagogy
        - The person must be link to requirement entity
        - The person can be a faculty or a central manager
        - The person can be a tutor:
            - The learning unit must have its flag summary_locked to false
            - The person must have an attribution for the learning unit year
            - The attribution must have its flag summary responsible to true.

    :param learning_unit_year: LearningUnitYear
    :param person: Person
    :return: bool
    """
    # Case Tutor: We need to check if today is between submission date
    if tutor.is_tutor(person.user):
        return CanUserEditEducationalInformation(
            user=person.user,
            learning_unit_year_id=learning_unit_year.id
        ).is_valid()

    if person.user.has_perm('base.can_edit_learningunit_pedagogy', learning_unit_year):
        return True

    return False


# TODO : migrate with tutor role creation
def is_eligible_to_update_learning_unit_pedagogy_force_majeure_section(learning_unit_year, person):
    if not is_year_editable(learning_unit_year, raise_exception=False):
        return False

    # Case Tutor: We need to check if today is between submission date of force majeure section
    if tutor.is_tutor(person.user):
        return CanUserEditEducationalInformationForceMajeure(
            user=person.user,
            learning_unit_year_id=learning_unit_year.id
        ).is_valid()

    if person.user.has_perm('base.can_edit_learningunit_pedagogy', learning_unit_year):
        return True

    return False


# TODO : migrate with tutor role creation
def _is_tutor_summary_responsible_of_learning_unit_year(*, user, learning_unit_year_id, **kwargs):
    if not _is_tutor_attributed_to_the_learning_unit(user, learning_unit_year_id):
        raise PermissionDenied(_("You are not attributed to this learning unit."))


# TODO : migrate with tutor role creation
def _is_learning_unit_year_summary_editable(*, learning_unit_year_id, **kwargs):
    if isinstance(learning_unit_year_id, LearningUnitYear):
        value = True
    else:
        value = LearningUnitYear.objects.filter(pk=learning_unit_year_id, summary_locked=False).exists()

    if not value:
        raise PermissionDenied(_("The learning unit's description fiche is not editable."))


# TODO : migrate with tutor role creation
def _is_calendar_opened_to_edit_educational_information(*, learning_unit_year_id, **kwargs):
    submission_dates = find_educational_information_submission_dates_of_learning_unit_year(learning_unit_year_id)
    permission_denied_msg = _("Not in period to edit description fiche.")
    if not submission_dates:
        raise PermissionDenied(permission_denied_msg)

    now = datetime.datetime.now(tz=get_tzinfo())
    value = convert_date_to_datetime(submission_dates["start_date"]) <= now <= \
        convert_date_to_datetime(submission_dates["end_date"])
    if not value:
        raise PermissionDenied(permission_denied_msg)


# TODO : migrate with tutor role creation
def _is_calendar_opened_to_edit_educational_information_force_majeure_section(*, learning_unit_year_id, **kwargs):
    submission_dates = find_educational_information_force_majeure_submission_dates_of_learning_unit_year(
        learning_unit_year_id
    )
    permission_denied_msg = _("Not in period to edit force majeure section.")
    if not submission_dates:
        raise PermissionDenied(permission_denied_msg)

    now = datetime.datetime.now(tz=get_tzinfo())
    value = convert_date_to_datetime(submission_dates["start_date"]) <= now <= \
        convert_date_to_datetime(submission_dates["end_date"])
    if not value:
        raise PermissionDenied(permission_denied_msg)


# TODO : migrate with tutor role creation
class CanUserEditEducationalInformation(BasePerm):
    predicates = (
        _is_tutor_summary_responsible_of_learning_unit_year,
        _is_learning_unit_year_summary_editable,
        _is_calendar_opened_to_edit_educational_information
    )


# TODO : migrate with tutor role creation
class CanUserEditEducationalInformationForceMajeure(BasePerm):
    predicates = (
        _is_tutor_summary_responsible_of_learning_unit_year,
        _is_learning_unit_year_summary_editable,
        _is_calendar_opened_to_edit_educational_information_force_majeure_section
    )


# TODO : migrate with tutor role creation
def find_educational_information_submission_dates_of_learning_unit_year(learning_unit_year_id):
    requirement_entity_version = find_last_requirement_entity_version(
        learning_unit_year_id=learning_unit_year_id,
    )
    if requirement_entity_version is None:
        return {}

    return find_summary_course_submission_dates_for_entity_version(
        entity_version=requirement_entity_version,
        ac_year=LearningUnitYear.objects.get(pk=learning_unit_year_id).academic_year
    )


# TODO : migrate with tutor role creation
def find_educational_information_force_majeure_submission_dates_of_learning_unit_year(learning_unit_year_id):
    requirement_entity_version = find_last_requirement_entity_version(
        learning_unit_year_id=learning_unit_year_id,
    )
    if requirement_entity_version is None:
        return {}

    return entity_calendar.find_interval_dates_for_entity(
        ac_year=LearningUnitYear.objects.get(pk=learning_unit_year_id).academic_year,
        reference=AcademicCalendarTypes.SUMMARY_COURSE_SUBMISSION_FORCE_MAJEURE.name,
        entity=requirement_entity_version.entity
    )


# TODO : migrate with tutor role creation
def find_last_requirement_entity_version(learning_unit_year_id):
    now = datetime.datetime.now(get_tzinfo())
    # TODO :: merge code below to get only 1 hit on database
    requirement_entity_id = LearningUnitYear.objects.filter(
        pk=learning_unit_year_id
    ).select_related(
        'learning_container_year'
    ).only(
        'learning_container_year'
    ).get().learning_container_year.requirement_entity_id
    try:
        return EntityVersion.objects.current(now).filter(entity=requirement_entity_id).get()
    except EntityVersion.DoesNotExist:
        return None


# TODO : migrate with tutor role creation
def is_year_editable(learning_unit_year, raise_exception):
    result = learning_unit_year.academic_year.year > settings.YEAR_LIMIT_LUE_MODIFICATION
    msg = "{}.  {}".format(
        _("You can't modify learning unit under year : %(year)d") %
        {"year": settings.YEAR_LIMIT_LUE_MODIFICATION + 1},
        _("Modifications should be made in EPC for year %(year)d") %
        {"year": learning_unit_year.academic_year.year},
    )
    can_raise_exception(raise_exception, result, msg)
    return result


# TODO : migrate with tutor role creation
def can_raise_exception(raise_exception, result, msg):
    if raise_exception and not result:
        raise PermissionDenied(msg)
