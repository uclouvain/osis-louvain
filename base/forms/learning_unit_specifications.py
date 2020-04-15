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
from ckeditor.widgets import CKEditorWidget
from django import forms
from django.conf import settings
from django.db.models import OuterRef, Min, Subquery

from base.business.learning_unit import get_academic_year_postponement_range
from base.forms.common import set_trans_txt
from base.models.learning_unit_year import LearningUnitYear
from base.models.proposal_learning_unit import ProposalLearningUnit
from cms.enums import entity_name
from cms.models import translated_text
from cms.models.translated_text import TranslatedText


class LearningUnitSpecificationsForm(forms.Form):
    learning_unit_year = language = None

    def __init__(self, learning_unit_year, language, *args, **kwargs):
        self.learning_unit_year = learning_unit_year
        self.language = language
        self.refresh_data()
        super(LearningUnitSpecificationsForm, self).__init__(*args, **kwargs)

    def refresh_data(self):
        language_iso = self.language[0]
        texts_list = translated_text.search(entity=entity_name.LEARNING_UNIT_YEAR,
                                            reference=self.learning_unit_year.id,
                                            language=language_iso) \
            .exclude(text__isnull=True)

        set_trans_txt(self, texts_list)


class LearningUnitSpecificationsEditForm(forms.Form):
    trans_text_fr = forms.CharField(widget=CKEditorWidget(config_name='minimal'), required=False)
    trans_text_en = forms.CharField(widget=CKEditorWidget(config_name='minimal'), required=False)
    cms_fr_id = forms.IntegerField(widget=forms.HiddenInput, required=True)
    cms_en_id = forms.IntegerField(widget=forms.HiddenInput, required=True)

    def __init__(self, *args, **kwargs):
        self.postponement = bool(int(args[0]['postpone'])) if args else False
        self.learning_unit_year = kwargs.pop('learning_unit_year', None)
        self.text_label = kwargs.pop('text_label', None)
        self.has_proposal = ProposalLearningUnit.objects.filter(learning_unit_year=self.learning_unit_year).exists()
        super(LearningUnitSpecificationsEditForm, self).__init__(*args, **kwargs)

    def load_initial(self):
        for code, label in settings.LANGUAGES:
            value = self._get_or_create_translated_text(code)
            vars()['value_{}'.format(code[:2])] = value
            self.fields['cms_{}_id'.format(code[:2])].initial = value.id
            self.fields['trans_text_{}'.format(code[:2])].initial = value.text

    def _get_or_create_translated_text(self, language):
        return translated_text.get_or_create(
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference=self.learning_unit_year.id,
            language=language,
            text_label=self.text_label
        )

    def save(self):
        self._save_translated_text()
        return self.text_label, self.last_postponed_academic_year

    def _get_ac_year_postponement_range(self):
        ac_year_postponement_range = get_academic_year_postponement_range(self.learning_unit_year)
        if self.learning_unit_year.min_proposal_year:
            return ac_year_postponement_range.exclude(year__gte=self.learning_unit_year.min_proposal_year)
        return ac_year_postponement_range

    def _save_translated_text(self):
        proposal_years = ProposalLearningUnit.objects.filter(
            learning_unit_year__learning_unit=OuterRef('learning_unit'),
            learning_unit_year__academic_year__year__gt=OuterRef('academic_year__year')
        ).values('learning_unit_year__academic_year__year')
        for code, label in settings.LANGUAGES:
            self.trans_text = TranslatedText.objects.get(pk=self.cleaned_data['cms_{}_id'.format(code[:2])])
            self.trans_text.text = self.cleaned_data.get('trans_text_{}'.format(code[:2]))
            self.text_label = self.trans_text.text_label
            self.trans_text.save()

            self.learning_unit_year = LearningUnitYear.objects.select_related('academic_year').prefetch_related(
                'learning_unit__learningunityear_set'
            ).annotate(
                min_proposal_year=Min(Subquery(proposal_years))
            ).get(id=self.trans_text.reference)

            self.last_postponed_academic_year = None
            if not self.learning_unit_year.academic_year.is_past and self.postponement:
                ac_year_postponement_range = self._get_ac_year_postponement_range()
                self.last_postponed_academic_year = ac_year_postponement_range.last()
                cms = {"language": self.trans_text.language,
                       "text_label": self.text_label,
                       "text": self.trans_text.text
                       }
                update_future_luy(ac_year_postponement_range, self.learning_unit_year, cms)


def update_future_luy(ac_year_postponement_range, luy, cms):
    for ac in ac_year_postponement_range:
        try:
            next_luy = LearningUnitYear.objects.get(
                academic_year=ac,
                acronym=luy.acronym,
                learning_unit=luy.learning_unit
            )
        except LearningUnitYear.DoesNotExist:
            continue

        TranslatedText.objects.update_or_create(
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference=next_luy.id,
            language=cms.get("language"),
            text_label=cms.get("text_label"),
            defaults={'text': cms.get("text")}
        )
