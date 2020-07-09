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
from django import forms
from django.db.models import Q
from django.utils import timezone

from base.models.entity_version import EntityVersion
from base.models.enums.organization_type import MAIN, ACADEMIC_PARTNER


class EntitiesVersionChoiceField(forms.ModelChoiceField):
    entity_version = None

    def __init__(self, queryset, *args, **kwargs):
        queryset = queryset.select_related('entity__organization')
        super().__init__(queryset, *args, **kwargs)

    def label_from_instance(self, obj):
        return obj.verbose_title

    def clean(self, value):
        ev_data = super().clean(value)
        self.entity_version = ev_data
        return ev_data.entity if ev_data else None


def find_additional_requirement_entities_choices():
    date = timezone.now()
    return EntityVersion.objects.current(date).filter(
        Q(entity__organization__type=MAIN) |
        (Q(entity__organization__type=ACADEMIC_PARTNER) & Q(entity__organization__is_current_partner=True))
    ).select_related('entity', 'entity__organization').order_by('acronym')
