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
from django.utils.translation import gettext_lazy as _

from base.business.learning_unit import get_academic_year_postponement_range
from base.models.learning_achievement import LearningAchievement
from base.models.learning_unit_year import LearningUnitYear
from base.models.proposal_learning_unit import ProposalLearningUnit
from cms.enums import entity_name
from cms.models import translated_text
from cms.models.text_label import TextLabel
from osis_common.utils.models import get_object_or_none
from reference.models.language import EN_CODE_LANGUAGE, Language


def update_themes_discussed_changed_field_in_cms(learning_unit_year):
    txt_label = get_object_or_none(
        TextLabel,
        label='themes_discussed'
    )
    if txt_label:
        for lang in settings.LANGUAGES:
            translated_text.update_or_create(
                entity=entity_name.LEARNING_UNIT_YEAR,
                reference=learning_unit_year.id,
                text_label=txt_label,
                language=lang[0],
                defaults={}
            )


class LearningAchievementEditForm(forms.ModelForm):
    text_fr = forms.CharField(
        widget=CKEditorWidget(config_name='minimal'),
        required=False,
        label=_('French')
    )
    text_en = forms.CharField(
        widget=CKEditorWidget(config_name='minimal'),
        required=False,
        label=_('English')
    )

    class Meta:
        model = LearningAchievement
        fields = ['code_name', 'text_fr', 'text_en']

    def __init__(self, data=None, initial=None, **kwargs):
        initial = initial or {}
        self.postponement = bool(int(data['postpone'])) if data else False
        self.luy = kwargs.pop('luy', None)
        self.code = kwargs.pop('code', '')
        self.consistency_id = kwargs.pop('consistency_id')
        self.order = kwargs.pop('order', None)
        self.has_proposal = ProposalLearningUnit.objects.filter(learning_unit_year=self.luy).exists()
        super().__init__(data, initial=initial, **kwargs)

        self._get_code_name_disabled_status()
        for key, value in initial.items():
            setattr(self.instance, key, value)
        self.load_initial()

    def load_initial(self):
        self.value = None
        for code, label in settings.LANGUAGES:
            value = get_object_or_none(
                LearningAchievement,
                learning_unit_year__id=self.luy.id,
                consistency_id=self.consistency_id,
                language=Language.objects.get(code=code[:2].upper())
            )
            if value:
                self.value = value
                self.fields['text_{}'.format(code[:2])].initial = self.value.text
                self.fields['code_name'].initial = self.value.code_name

    def _get_code_name_disabled_status(self):
        if self.instance.pk and self.instance.language.code == EN_CODE_LANGUAGE:
            self.fields["code_name"].disabled = True

    def save(self, commit=True):
        return self._save_translated_text()

    def _get_ac_year_postponement_range(self, first_proposal_year):
        ac_year_postponement_range = get_academic_year_postponement_range(self.luy)
        if first_proposal_year:
            return ac_year_postponement_range.exclude(year__gte=first_proposal_year)
        return ac_year_postponement_range

    def _save_translated_text(self):
        first_proposal_year = ProposalLearningUnit.objects.filter(
            learning_unit_year__learning_unit=self.luy.learning_unit,
            learning_unit_year__academic_year__year__gt=self.luy.academic_year.year
        ).values_list('learning_unit_year__academic_year__year', flat=True).first()
        for code, label in settings.LANGUAGES:
            self.achievement, _ = LearningAchievement.objects.select_related(
                'learning_unit_year__academic_year').prefetch_related(
                'learning_unit_year__learning_unit__learningunityear_set'
            ).get_or_create(
                learning_unit_year_id=self.luy.id,
                language=Language.objects.get(code=code[:2].upper()),
                consistency_id=self.consistency_id,
                order=self.order
            )
            self.achievement.code_name = self.cleaned_data.get('code_name')
            self.achievement.text = self.cleaned_data.get('text_{}'.format(code[:2]))
            self.achievement.save()

            self.last_postponed_academic_year = None
            if not self.achievement.learning_unit_year.academic_year.is_past and self.postponement:
                ac_year_postponement_range = self._get_ac_year_postponement_range(first_proposal_year)
                self.last_postponed_academic_year = ac_year_postponement_range.last()
                update_future_luy(ac_year_postponement_range, self.achievement)

        # For sync purpose, we need to trigger for the first year
        # an update of the THEMES_DISCUSSED cms when we update learning achievement
        update_themes_discussed_changed_field_in_cms(self.achievement.learning_unit_year)
        return self.achievement, self.last_postponed_academic_year

    def clean_code_name(self):
        code_name = self.cleaned_data.pop('code_name')
        objects = LearningAchievement.objects.filter(
            code_name=code_name,
            learning_unit_year_id=self.luy.id,
        )
        if code_name and objects.exists() and self.value not in objects:
            raise forms.ValidationError(_("This code already exists for this learning unit"), code='invalid')
        return code_name


def update_future_luy(ac_year_postponement_range, achievement):
    for ac in ac_year_postponement_range:
        luy = achievement.learning_unit_year
        try:
            next_luy = LearningUnitYear.objects.get(
                academic_year=ac,
                acronym=luy.acronym,
                learning_unit=luy.learning_unit
            )
        except LearningUnitYear.DoesNotExist:
            continue

        # For sync purpose, we need to trigger for the following years
        # an update of the THEMES_DISCUSSED cms when we update learning achievement
        update_themes_discussed_changed_field_in_cms(next_luy)

        LearningAchievement.objects.update_or_create(
            consistency_id=achievement.consistency_id,
            language=achievement.language,
            learning_unit_year=next_luy,
            defaults={'text': achievement.text, 'code_name': achievement.code_name}
        )
