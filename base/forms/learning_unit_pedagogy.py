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
from django import forms
from django.utils.safestring import mark_safe
from ckeditor.widgets import CKEditorWidget

from base.models.learning_unit_year import LearningUnitYear
from cms.enums import entity_name
from cms.models import translated_text


class LearningUnitPedagogyForm(forms.Form):
    learning_unit_year = language = None
    text_labels_name = ['resume', 'bibliography', 'teaching_methods', 'evaluation_methods',
                        'other_informations', 'online_resources']

    def __init__(self, *args, **kwargs):
        self.learning_unit_year = kwargs.pop('learning_unit_year', None)
        self.language = kwargs.pop('language', None)
        self.load_initial()
        super(LearningUnitPedagogyForm, self).__init__(*args, **kwargs)

    def load_initial(self):
        translated_texts_list = self._get_all_translated_text_related()

        for trans_txt in translated_texts_list:
            text_label = trans_txt.text_label.label
            text = trans_txt.text if trans_txt.text else ""
            setattr(self, text_label, mark_safe(text))

    def _get_all_translated_text_related(self):
        language_iso = self.language[0]

        return translated_text.search(entity=entity_name.LEARNING_UNIT_YEAR,
                                      reference=self.learning_unit_year.id,
                                      language=language_iso,
                                      text_labels_name=self.text_labels_name)


class LearningUnitPedagogyEditForm(forms.Form):
    trans_text = forms.CharField(widget=CKEditorWidget(config_name='minimal_plus_headers'), required=False)
    cms_id = forms.IntegerField(widget=forms.HiddenInput, required=True)

    def __init__(self, *args, **kwargs):
        self.learning_unit_year = kwargs.pop('learning_unit_year', None)
        self.language_iso = kwargs.pop('language', None)
        self.text_label = kwargs.pop('text_label', None)
        super(LearningUnitPedagogyEditForm, self).__init__(*args, **kwargs)

    def load_initial(self):
        value = translated_text.get_or_create(entity=entity_name.LEARNING_UNIT_YEAR,
                                              reference=self.learning_unit_year.id,
                                              language=self.language_iso,
                                              text_label=self.text_label)
        self.fields['cms_id'].initial = value.id
        self.fields['trans_text'].initial = value.text

    def save(self):
        cleaned_data = self.cleaned_data
        trans_text = translated_text.find_by_id(cleaned_data['cms_id'])
        trans_text.text = cleaned_data.get('trans_text')
        trans_text.save()


class SummaryEditableModelForm(forms.ModelForm):
    class Meta:
        model = LearningUnitYear
        fields = ['summary_editable']
