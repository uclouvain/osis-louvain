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

from cms.enums import entity_name
from cms.models import translated_text


class EducationGroupPedagogyEditForm(forms.Form):
    trans_text = forms.CharField(widget=CKEditorWidget(config_name='reddot'), required=False)
    cms_id = forms.IntegerField(widget=forms.HiddenInput, required=True)

    def __init__(self, *args, **kwargs):
        self.education_group_year = kwargs.pop('education_group_year', None)
        self.language_iso = kwargs.pop('language', None)
        self.text_label = kwargs.pop('text_label', None)
        super().__init__(*args, **kwargs)

    def load_initial(self):
        value = translated_text.get_or_create(entity=entity_name.OFFER_YEAR,
                                              reference=self.education_group_year.id,
                                              language=self.language_iso,
                                              text_label=self.text_label)
        self.fields['cms_id'].initial = value.id
        self.fields['trans_text'].initial = value.text

    def save(self):
        cleaned_data = self.cleaned_data
        trans_text = translated_text.find_by_id(cleaned_data['cms_id'])
        trans_text.text = cleaned_data.get('trans_text')
        trans_text.save()
