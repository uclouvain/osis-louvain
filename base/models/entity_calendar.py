##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db import models

from base.models import academic_calendar
from base.models import entity_version
from base.models.abstracts.abstract_calendar import AbstractCalendar
from base.models.academic_year import current_academic_year, starting_academic_year
from osis_common.models.osis_model_admin import OsisModelAdmin


class EntityCalendarAdmin(OsisModelAdmin):
    list_display = ('academic_calendar', 'entity', 'start_date', 'end_date', 'changed')
    raw_id_fields = ('entity',)
    list_filter = ('academic_calendar__academic_year', 'academic_calendar__reference')


class EntityCalendar(AbstractCalendar):
    entity = models.ForeignKey('Entity')

    class Meta:
        unique_together = ('academic_calendar', 'entity')

    def __str__(self):
        return "{} - {}".format(self.academic_calendar, self.entity)


def find_by_entity_and_reference(entity_id, reference, academic_year=None):
    if not academic_year:
        academic_year = starting_academic_year()
    try:
        return EntityCalendar.objects.filter(
            entity_id=entity_id,
            academic_calendar__academic_year=academic_year,
            academic_calendar__reference=reference
        ).select_related('entity', 'academic_calendar__academic_year').get()
    except ObjectDoesNotExist:
        return None


def find_interval_dates_for_entity(ac_year, reference, entity):
    return next((
        date_computed for entity_id, date_computed in build_calendar_by_entities(ac_year, reference).items()
        if entity.id == entity_id
    ), None)


def build_calendar_by_entities(ac_year, reference):
    """
    This function will compute date for each entity. If entity calendar not exist,
    get default date to academic calendar
    """
    entity_structure = entity_version.build_current_entity_version_structure_in_memory(date=ac_year.end_date)
    entities_id = list(entity_structure.keys())
    ac_calendar = academic_calendar.get_by_reference_and_academic_year(reference, ac_year)
    all_entities_calendars = EntityCalendar.objects.filter(entity__in=entities_id, academic_calendar=ac_calendar) \
        .select_related('entity')

    # Specific date for an entity [record found on entity calendar]
    entity_calendar_computed = {}
    for entity_calendar in all_entities_calendars:
        # FIXME: We should use date OR datetime in all database model
        entity_calendar_computed[entity_calendar.entity_id] = {
            'start_date': entity_calendar.start_date.date(),
            'end_date': entity_calendar.end_date.date(),
        }
        entities_id.remove(entity_calendar.entity_id)

    default_dates = {'start_date': ac_calendar.start_date, 'end_date': ac_calendar.end_date}
    entity_calendar_computed.update({
        entity_id: _get_start_end_date_of_parent(entity_id, entity_structure, entity_calendar_computed, default_dates)
        for entity_id in entities_id
    })
    return entity_calendar_computed


def _get_start_end_date_of_parent(entity_id, entity_structure, entity_calendar_computed, default_date):
    # Case found start/end date for entity
    if entity_id in entity_calendar_computed:
        return entity_calendar_computed[entity_id]

    # Case have parent, lookup start/end date in parent
    if entity_structure[entity_id]['entity_version_parent']:
        parent_entity_id = entity_structure[entity_id]['entity_version_parent'].entity_id
        return _get_start_end_date_of_parent(parent_entity_id, entity_structure, entity_calendar_computed, default_date)

    # Case no entity calendar at all
    return default_date
