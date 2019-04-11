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
from ckeditor.widgets import CKEditorWidget
from django import forms
from django.conf import settings
from django.db.transaction import atomic
from django.utils.translation import ugettext_lazy as _

from base.business.learning_unit import CMS_LABEL_PEDAGOGY_FR_ONLY
from base.business.learning_units.pedagogy import is_pedagogy_data_must_be_postponed, save_teaching_material
from base.models import learning_unit_year
from base.models.teaching_material import TeachingMaterial
from cms.enums import entity_name
from cms.models import translated_text


class LearningUnitPedagogyEditForm(forms.Form):
    trans_text = forms.CharField(widget=CKEditorWidget(config_name='minimal_plus_headers'), required=False)
    cms_id = forms.IntegerField(widget=forms.HiddenInput, required=True)

    def __init__(self, *args, **kwargs):
        self.learning_unit_year = kwargs.pop('learning_unit_year', None)
        self.language_iso = kwargs.pop('language', None)
        self.text_label = kwargs.pop('text_label', None)
        super().__init__(*args, **kwargs)

    def load_initial(self):
        value = self._get_or_create_translated_text()
        self.fields['cms_id'].initial = value.id
        self.fields['trans_text'].initial = value.text

    @atomic
    def save(self):
        trans_text = self._get_or_create_translated_text()
        start_luy = learning_unit_year.get_by_id(trans_text.reference)

        reference_ids = [start_luy.id]
        if is_pedagogy_data_must_be_postponed(start_luy):
            reference_ids += [luy.id for luy in start_luy.find_gt_learning_units_year()]

        for reference_id in reference_ids:
            if trans_text.text_label.label in CMS_LABEL_PEDAGOGY_FR_ONLY:
                # In case of FR only CMS field, also save text to corresponding EN field
                languages = [language[0] for language in settings.LANGUAGES]
            else:
                languages = [trans_text.language]

            self._update_or_create_translated_texts(languages, reference_id, trans_text)

    def _update_or_create_translated_texts(self, languages, reference_id, trans_text):
        for language in languages:
            translated_text.update_or_create(
                entity=trans_text.entity,
                reference=reference_id,
                language=language,
                text_label=trans_text.text_label,
                defaults={'text': self.cleaned_data['trans_text']}
            )

    def _get_or_create_translated_text(self):
        if hasattr(self, 'cleaned_data'):
            cms_id = self.cleaned_data['cms_id']
            return translated_text.find_by_id(cms_id)
        return translated_text.get_or_create(
            entity=entity_name.LEARNING_UNIT_YEAR,
            reference=self.learning_unit_year.id,
            language=self.language_iso,
            text_label=self.text_label
        )


class TeachingMaterialModelForm(forms.ModelForm):
    mandatory = forms.ChoiceField(widget=forms.RadioSelect,
                                  choices=[
                                      (True, _('Yes')),
                                      (False, _('No'))
                                  ],
                                  label=_('Is this teaching material mandatory?'),
                                  required=True)

    class Meta:
        model = TeachingMaterial
        fields = ['title', 'mandatory']

    def save(self, learning_unit_year, commit=True):
        instance = super().save(commit=False)
        instance.learning_unit_year = learning_unit_year
        return save_teaching_material(instance)
