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
from ckeditor.fields import RichTextFormField
from ckeditor_uploader.fields import RichTextUploadingFormField
from django import forms

from base.models.admission_condition import CONDITION_ADMISSION_ACCESSES

PARAMETERS_FOR_RICH_TEXT = dict(required=False, config_name='minimal')
PARAMETERS_FOR_RICH_TEXT_UPLOAD = dict(required=False, config_name='minimal_upload')


class UpdateLineForm(forms.Form):
    admission_condition_line = forms.IntegerField(widget=forms.HiddenInput())
    section = forms.CharField(widget=forms.HiddenInput())
    language = forms.CharField(widget=forms.HiddenInput())
    diploma = forms.CharField(widget=forms.Textarea, required=False)
    conditions = RichTextFormField(**PARAMETERS_FOR_RICH_TEXT)
    access = forms.ChoiceField(choices=CONDITION_ADMISSION_ACCESSES, required=False)
    remarks = RichTextFormField(**PARAMETERS_FOR_RICH_TEXT)


class UpdateTextForm(forms.Form):
    text_fr = RichTextUploadingFormField(**PARAMETERS_FOR_RICH_TEXT_UPLOAD)
    text_en = RichTextUploadingFormField(**PARAMETERS_FOR_RICH_TEXT_UPLOAD)
    section = forms.CharField(widget=forms.HiddenInput())
