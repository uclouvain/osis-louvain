##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db.models import Q
from django.forms import ModelForm, Textarea
from assistant import models as mdl
from base.models import structure, academic_year
from django.forms.models import inlineformset_factory


class MandateForm(ModelForm):
    comment = forms.CharField(required=False, widget=Textarea(attrs={'rows': '3', 'cols': '50'}))
    absences = forms.CharField(required=False, widget=Textarea(attrs={'rows': '3', 'cols': '50'}))
    other_status = forms.CharField(required=False)
    renewal_type=forms.ChoiceField(choices=mdl.assistant_mandate.AssistantMandate.RENEWAL_TYPE_CHOICES)
    assistant_type=forms.ChoiceField(choices=mdl.assistant_mandate.AssistantMandate.ASSISTANT_TYPE_CHOICES)
    sap_id = forms.CharField(required=True, max_length=12, strip=True)
    contract_duration = forms.CharField(required=True, max_length=30, strip=True)
    contract_duration_fte = forms.CharField(required=True, max_length=30, strip=True)

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('comment', 'absences', 'other_status', 'renewal_type', 'assistant_type', 'sap_id',
                  'contract_duration', 'contract_duration_fte')

    
class MandateStructureForm(ModelForm):
    class Meta:
        model = mdl.mandate_structure.MandateStructure
        fields = ('structure', 'assistant_mandate')

        
def get_field_qs(field, **kwargs):
        if field.name == 'structure':
            return forms.ModelChoiceField(queryset=structure.Structure.objects.filter(Q(type='INSTITUTE') |
                                                                                      Q(type='FACULTY')))
        return field.formfield(**kwargs)

    
StructureInLineFormSet = inlineformset_factory(mdl.assistant_mandate.AssistantMandate, 
                                               mdl.mandate_structure.MandateStructure,
                                               formfield_callback=get_field_qs,
                                               fields=('structure', 'assistant_mandate'),
                                               extra=2,
                                               can_delete=True,
                                               min_num=1,
                                               max_num=2)


class MandatesArchivesForm(ModelForm):
    academic_year = forms.ModelChoiceField(queryset=academic_year.AcademicYear.objects.all(),
                                           widget=forms.Select(attrs={"onChange": 'submit()'}))

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('academic_year',)
