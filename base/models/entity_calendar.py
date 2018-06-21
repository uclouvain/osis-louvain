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

from base.models.abstracts.abstract_calendar import AbstractCalendar
from base.models.academic_year import current_academic_year
from osis_common.models.osis_model_admin import OsisModelAdmin


class EntityCalendarAdmin(OsisModelAdmin):
    list_display = ('academic_calendar', 'entity', 'start_date', 'end_date', 'changed')
    raw_id_fields = ('entity', )
    list_filter = ('academic_calendar__academic_year', 'academic_calendar__reference')


class EntityCalendar(AbstractCalendar):
    entity = models.ForeignKey('Entity')

    class Meta:
        unique_together = ('academic_calendar', 'entity')

    def __str__(self):
        return "{} - {}".format(self.academic_calendar, self.entity)


def find_by_entity_and_reference_for_current_academic_year(entity_id, reference):
    try:
        return EntityCalendar.objects.filter(entity_id=entity_id,
                                             academic_calendar__academic_year=current_academic_year(),
                                             academic_calendar__reference=reference)\
            .select_related('entity', 'academic_calendar__academic_year').get()
    except ObjectDoesNotExist:
        return None


def find_by_reference_and_entity(a_reference, an_entity):
    try:
        return EntityCalendar.objects.get(academic_calendar__academic_year=current_academic_year(),
                                          academic_calendar__reference=a_reference,
                                          entity=an_entity)
    except ObjectDoesNotExist:
        return None
