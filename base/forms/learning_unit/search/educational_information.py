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
from django.db.models import OuterRef, Case, When, Value, Subquery, BooleanField
from django_filters import filters

from base.business.learning_unit import CMS_LABEL_PEDAGOGY
from base.forms.learning_unit.search.simple import LearningUnitFilter
from base.models import entity_calendar
from base.models.enums.academic_calendar_type import SUMMARY_COURSE_SUBMISSION
from base.views.learning_units.search.common import SearchTypes
from cms.enums.entity_name import LEARNING_UNIT_YEAR
from cms.models.translated_text import TranslatedText


class LearningUnitDescriptionFicheFilter(LearningUnitFilter):
    search_type = filters.CharFilter(
        field_name="acronym",
        method=lambda request, *args, **kwargs: request,
        widget=forms.HiddenInput,
        required=False,
        initial=SearchTypes.SUMMARY_LIST.value
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form.fields['with_entity_subordinated'].initial = True
        self.form.fields["academic_year"].required = True

    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'campus',
        ).prefetch_related(
            "learningcomponentyear_set",
        )

        translated_text_qs = TranslatedText.objects.filter(
            entity=LEARNING_UNIT_YEAR,
            text_label__label__in=CMS_LABEL_PEDAGOGY,
            changed__isnull=False,
            reference=OuterRef('pk')
        ).order_by("-changed")

        return queryset.annotate(
            last_translated_text_changed=Subquery(translated_text_qs.values('changed')[:1]),
        )

    @property
    def qs(self):
        queryset = super().qs
        if self.is_bound:
            queryset = self._compute_summary_status(queryset)
            queryset = queryset.select_related('learning_container_year__academic_year', 'academic_year')
        return queryset

    def _compute_summary_status(self, queryset):
        """
        This function will compute the summary status. First, we will take the entity calendar
        (or entity calendar parent and so one) of the requirement entity. If not found, the summary status is
        computed with the general Academic Calendar Object
        """
        entity_calendars_computed = entity_calendar.build_calendar_by_entities(
            self.form.cleaned_data['academic_year'].past(),
            SUMMARY_COURSE_SUBMISSION,
        )
        requirement_entities_ids = queryset.values_list('learning_container_year__requirement_entity', flat=True)

        summary_status_case_statment = [When(last_translated_text_changed__isnull=True, then=False)]
        for requirement_entity_id in set(requirement_entities_ids):
            start_summary_course_submission = entity_calendars_computed.get(requirement_entity_id, {}).get('start_date')
            if start_summary_course_submission is None:
                continue

            summary_status_case_statment.append(
                When(
                    learning_container_year__requirement_entity=requirement_entity_id,
                    last_translated_text_changed__gte=start_summary_course_submission,
                    then=True
                )
            )

        queryset = queryset.annotate(
            summary_status=Case(
                *summary_status_case_statment,
                default=Value(False),
                output_field=BooleanField()
            )
        )
        return queryset
