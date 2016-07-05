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
from django.utils.translation import ugettext as _
from django.forms import BaseModelFormSet
from django.db.models import Q
from django.forms import ModelForm, Textarea
from assistant import models as mdl
from base.models import structure, academic_year
from django.forms.models import inlineformset_factory
from assistant.models import assistant_mandate, academic_assistant,\
    assistant_document


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


class HorizontalRadioRenderer(forms.RadioSelect.renderer):
    def render(self):
        return u'\n'.join([u'%s\n' % w for w in self])


class AssistantFormPart1(forms.Form):
    inscription = forms.ChoiceField(
            choices=mdl.academic_assistant.AcademicAssistant.PHD_INSCRIPTION_CHOICES,
            widget=forms.RadioSelect(renderer=HorizontalRadioRenderer))
    expected_phd_date = forms.DateField(widget=forms.DateInput(format='%d/%m/%Y',
                                        attrs={'placeholder': 'dd/mm/yyyy'}),
                                        input_formats='%d/%m/%Y')
    phd_inscription_date = forms.DateField(widget=forms.DateInput(format='%d/%m/%Y',
                                           attrs={'placeholder':'dd/mm/yyyy'}),
                                           input_formats='%d/%m/%Y')
    confirmation_test_date = forms.DateField(widget=forms.DateInput(format='%d/%m/%Y',
                                             attrs={'placeholder': 'dd/mm/yyyy'}),
                                             input_formats='%d/%m/%Y')
    thesis_date = forms.DateField(widget=forms.DateInput(format='%d/%m/%Y',
                                  attrs={'placeholder': 'dd/mm/yyyy'}),
                                  input_formats='%d/%m/%Y')
    supervisor = forms.CharField(widget=forms.TextInput(
                                 attrs={'placeholder': 'firstname.lastname@uclouvain.be', 'size': '30'}))
    external_functions = forms.CharField(widget=forms.Textarea(attrs={'cols': '40', 'rows': '2'}))
    external_contract = forms.CharField(widget=forms.Textarea(attrs={'cols': '40', 'rows': '2'}))
    justification = forms.CharField(widget=forms.Textarea(attrs={'cols': '40', 'rows': '2'}))


class MandatesArchivesForm(ModelForm):
    academic_year = forms.ModelChoiceField(queryset=academic_year.AcademicYear.objects.all(),
                                           widget=forms.Select(attrs={"onChange": 'submit()'}))

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('academic_year',)


class PhdFilesFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(PhdFilesFormSet, self).__init__(*args, **kwargs)
        self.queryset = assistant_document.AssistantDocument.objects.filter(doc_type='PHD')


class AssistantFormPart3(ModelForm):
    phd_inscription_date = forms.DateField(required=False, 
                                           widget=forms.DateInput(format='%d/%m/%Y',
                                                                  attrs={'placeholder': 'dd/mm/yyyy'}),
                                                                  input_formats=['%d/%m/%Y'])
    confirmation_test_date = forms.DateField(required=False, 
                                             widget=forms.DateInput(format='%d/%m/%Y',
                                                                    attrs={'placeholder': 'dd/mm/yyyy'}),
                                                                    input_formats=['%d/%m/%Y'])
    thesis_title = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '2'}))
    remark = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '4'}))

    class Meta:
        model = mdl.academic_assistant.AcademicAssistant
        fields = ('phd_inscription_date', 'confirmation_test_date', 'thesis_title',
                  'remark')

  
class AssistantDocumentForm(ModelForm):
    file = forms.FileField(required=True, widget=forms.ClearableFileInput(attrs={'multiple': False}))
    mandate = forms.ModelChoiceField(required=True,queryset=assistant_mandate.AssistantMandate.objects.all(),
                                           widget=forms.HiddenInput())
    doc_type = forms.ChoiceField(required=True,
            choices=mdl.assistant_document.AssistantDocument.DOC_TYPE_CHOICES,
            widget=forms.HiddenInput())
    assistant = forms.ModelChoiceField(required=True,queryset=academic_assistant.AcademicAssistant.objects.all(),
                                           widget=forms.HiddenInput())

    class Meta:
        model = mdl.assistant_document.AssistantDocument
        fields = ('file','mandate','assistant','doc_type')
    
    def delete(self, *args, **kwargs):
        self.file.delete()
        super(AssistantDocumentForm, self).delete(*args, **kwargs)
        
    def clean_file(self):
        file = self.cleaned_data['file']
        try :
            if  file.content_type != "application/pdf":
                raise forms.ValidationError(_('must_upload_pdf') ,code='invalid')
        except AttributeError:
            pass   
        return file
    
FilesInLineFormSet = inlineformset_factory(mdl.assistant_mandate.AssistantMandate, 
                                               mdl.assistant_document.AssistantDocument,
                                               fields=('file','assistant','doc_type'),
                                               can_delete=True,
                                               extra=0,
                                               max_num=5,
                                               min_num=0,
                                               form = AssistantDocumentForm
                                               )  
