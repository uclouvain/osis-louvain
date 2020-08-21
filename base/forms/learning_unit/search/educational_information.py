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
from django.db.models.expressions import RawSQL
from django_filters import filters

from base.business.learning_unit import CMS_LABEL_PEDAGOGY
from base.forms.learning_unit.search.simple import LearningUnitFilter
from base.models import academic_calendar
from base.models.enums.academic_calendar_type import SUMMARY_COURSE_SUBMISSION
from base.views.learning_units.search.common import SearchTypes


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

        return queryset

    @property
    def qs(self):
        queryset = super().qs
        if self.is_bound:
            queryset = self._compute_summary_status(queryset)
            queryset = queryset.select_related('learning_container_year__academic_year', 'academic_year')
        return queryset

    def _compute_summary_status(self, queryset):
        ac_calendar = academic_calendar.get_by_reference_and_data_year(
            SUMMARY_COURSE_SUBMISSION,
            self.form.cleaned_data['academic_year']
        )

        extra_query = """
            EXISTS(
                SELECT * 
                FROM cms_translatedtext
                JOIN cms_textlabel ct on cms_translatedtext.text_label_id = ct.id
                JOIN reversion_version rv on rv.object_id::int = cms_translatedtext.id
                JOIN reversion_revision rr on rv.revision_id = rr.id
                WHERE ct.label in %s 
                    and rr.date_created >= %s 
                    and cms_translatedtext.reference = base_learningunityear.id
            )
        """

        return queryset.annotate(
            summary_status=RawSQL(
                extra_query,
                (tuple(CMS_LABEL_PEDAGOGY), ac_calendar and ac_calendar.start_date,)
            )
        )
