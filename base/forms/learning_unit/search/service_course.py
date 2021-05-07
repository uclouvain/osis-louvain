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
from django.utils.translation import gettext_lazy as _
from django_filters import filters

from base.business.entity_version import MainEntityStructure, load_main_entity_structure
from base.forms.learning_unit.search.simple import LearningUnitFilter
from base.models.academic_year import AcademicYear
from base.models.learning_unit_year import LearningUnitYear
from base.views.learning_units.search.common import SearchTypes


class ServiceCourseFilter(LearningUnitFilter):
    academic_year = filters.ModelChoiceFilter(
        queryset=AcademicYear.objects.all(),
        required=True,
        label=_('Ac yr.'),
        empty_label=None
    )
    search_type = filters.CharFilter(
        field_name="acronym",
        method=lambda request, *args, **kwargs: request,
        widget=forms.HiddenInput,
        required=False,
        initial=SearchTypes.SERVICE_COURSES_SEARCH.value
    )

    def filter_queryset(self, queryset):
        qs = super().filter_queryset(queryset)

        entity_structure = load_main_entity_structure()
        service_courses_ids = [luy.id for luy in qs if _is_service_course(luy, entity_structure)]
        return qs.filter(pk__in=service_courses_ids)


def _is_service_course(luy: 'LearningUnitYear', entity_structure: 'MainEntityStructure'):
    if not luy.learning_container_year.requirement_entity_id:
        return False
    if not luy.learning_container_year.allocation_entity_id:
        return False
    return not entity_structure.in_same_faculty(
        luy.learning_container_year.requirement_entity_id,
        luy.learning_container_year.allocation_entity_id
    )
