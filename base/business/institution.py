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
from django.shortcuts import get_object_or_404

from base.models import entity_calendar, academic_calendar, person_entity
from base.models import academic_year as mdl_academic_year
from base.models.entity import Entity
from base.models.enums import academic_calendar_type
from base.models.person import Person


def find_summary_course_submission_dates_for_entity_version(academic_year, entity_version):
    academic_calendar_instance = None
    current_entity_version = entity_version
    previous_academic_year = mdl_academic_year.find_academic_year_by_year(academic_year.year-1)
    while current_entity_version:
        academic_calendar_instance = entity_calendar.find_by_entity_and_reference_for_academic_year(
            previous_academic_year, current_entity_version.entity.id, academic_calendar_type.SUMMARY_COURSE_SUBMISSION)
        if academic_calendar_instance:
            break
        current_entity_version = current_entity_version.get_parent_version()

    if academic_calendar_instance is None:
        academic_calendar_instance = academic_calendar.get_by_reference_and_academic_year(
            academic_calendar_type.SUMMARY_COURSE_SUBMISSION, previous_academic_year)

    return {'start_date': academic_calendar_instance.start_date,
            'end_date': academic_calendar_instance.end_date}


def can_user_edit_educational_information_submission_dates_for_entity(a_user, an_entity):
    person = get_object_or_404(Person, user=a_user)
    return person.is_faculty_manager() and \
        person_entity.is_attached_entities(person, Entity.objects.filter(pk=an_entity.pk))
