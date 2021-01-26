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

from base.business.education_groups.admission_condition import postpone_admission_condition_line
from base.forms.utils.fields import OsisRichTextFormField
from base.models.admission_condition import CONDITION_ADMISSION_ACCESSES, AdmissionConditionLine


class UpdateLineForm(forms.Form):
    admission_condition_line = forms.IntegerField(widget=forms.HiddenInput())
    section = forms.CharField(widget=forms.HiddenInput())
    language = forms.CharField(widget=forms.HiddenInput())
    diploma = forms.CharField(widget=forms.Textarea, required=False)
    conditions = OsisRichTextFormField(required=False)
    access = forms.ChoiceField(choices=CONDITION_ADMISSION_ACCESSES, required=False)
    remarks = OsisRichTextFormField(required=False)


class SaveAdmissionLineMixin:
    def save(self, *args, **kwargs):
        instance = super().save(*args, **kwargs)
        if self.data.get("to_postpone"):
            postpone_admission_condition_line(instance.admission_condition.education_group_year, instance.section)
        return instance


class UpdateLineFrenchForm(SaveAdmissionLineMixin, forms.ModelForm):
    diploma = OsisRichTextFormField(required=False)
    conditions = OsisRichTextFormField(required=False)
    remarks = OsisRichTextFormField(required=False)

    class Meta:
        model = AdmissionConditionLine
        fields = ["access", "diploma", "conditions", "remarks"]


class UpdateLineEnglishForm(SaveAdmissionLineMixin, forms.ModelForm):
    diploma = OsisRichTextFormField(required=False)
    conditions_en = OsisRichTextFormField(required=False)
    remarks_en = OsisRichTextFormField(required=False)

    class Meta:
        model = AdmissionConditionLine
        fields = ["access", "diploma_en", "conditions_en", "remarks_en"]


class CreateLineFrenchForm(SaveAdmissionLineMixin, forms.ModelForm):
    diploma = OsisRichTextFormField(required=False)
    conditions = OsisRichTextFormField(required=False)
    remarks = OsisRichTextFormField(required=False)

    class Meta:
        model = AdmissionConditionLine
        fields = ["section", "access", "diploma", "conditions", "remarks"]
        widgets = {"section": forms.HiddenInput()}


class CreateLineEnglishForm(SaveAdmissionLineMixin, forms.ModelForm):
    diploma = OsisRichTextFormField(required=False)
    conditions_en = OsisRichTextFormField(required=False)
    remarks_en = OsisRichTextFormField(required=False)

    class Meta:
        model = AdmissionConditionLine
        fields = ["section", "access", "diploma_en", "conditions_en", "remarks_en"]
        widgets = {"section": forms.HiddenInput()}


class UpdateTextForm(forms.Form):
    text_fr = OsisRichTextFormField(required=False)
    text_en = OsisRichTextFormField(required=False)
    section = forms.CharField(widget=forms.HiddenInput())
