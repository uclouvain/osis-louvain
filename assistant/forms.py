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
from django.db.models import Q
from django.forms import ModelForm, Textarea
from assistant import models as mdl
from base.models import structure, academic_year, person, learning_unit_year
from django.forms.models import inlineformset_factory
from django.core.exceptions import ValidationError
from django.forms import widgets
from assistant.enums import reviewer_role
from assistant.models.enums import review_advice_choices, review_status


class MandateFileForm(forms.Form):
    file = forms.FileField(error_messages={'required': _('no_file_submitted')})

    def clean_file(self):
        file = self.cleaned_data['file']
        content_type = file.content_type.split('/')[1]
        valid_content_type = 'vnd.openxmlformats-officedocument.spreadsheetml.sheet' in content_type
        if ".xlsx" not in file.name or not valid_content_type:
            self.add_error('file', forms.ValidationError(_('file_must_be_xlsx'), code='invalid'))
        return file


class MandateForm(ModelForm):
    comment = forms.CharField(required=False, widget=Textarea(
        attrs={'rows': '4', 'cols': '80'}))
    absences = forms.CharField(required=False, widget=Textarea(
        attrs={'rows': '4', 'cols': '80'}))
    other_status = forms.CharField(max_length=50, required=False)
    renewal_type = forms.ChoiceField(
        choices=mdl.assistant_mandate.AssistantMandate.RENEWAL_TYPE_CHOICES)
    assistant_type = forms.ChoiceField(
        choices=mdl.assistant_mandate.AssistantMandate.ASSISTANT_TYPE_CHOICES)
    sap_id = forms.CharField(required=True, max_length=12, strip=True)
    contract_duration = forms.CharField(
        required=True, max_length=30, strip=True)
    contract_duration_fte = forms.CharField(
        required=True, max_length=30, strip=True)
    fulltime_equivalent = forms.NumberInput()

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('comment', 'absences', 'other_status', 'renewal_type', 'assistant_type', 'sap_id',
                  'contract_duration', 'contract_duration_fte', 'fulltime_equivalent')


class MandateStructureForm(ModelForm):
    class Meta:
        model = mdl.mandate_structure.MandateStructure
        fields = ('structure', 'assistant_mandate')


def get_field_qs(field, **kwargs):
    if field.name == 'structure':
        return forms.ModelChoiceField(queryset=structure.Structure.objects.filter(
            Q(type='INSTITUTE') | Q(type='POLE') | Q(type='PROGRAM_COMMISSION') |
            Q(type='FACULTY')).order_by('acronym'))
    return field.formfield(**kwargs)


structure_inline_formset = inlineformset_factory(mdl.assistant_mandate.AssistantMandate,
                                                 mdl.mandate_structure.MandateStructure,
                                                 formfield_callback=get_field_qs,
                                                 fields=('structure', 'assistant_mandate'),
                                                 extra=2, can_delete=True, min_num=1, max_num=4)


class HorizontalRadioRenderer(forms.RadioSelect.renderer):
    def render(self):
        return u'\n'.join([u'%s\n' % w for w in self])


class AssistantFormPart1(ModelForm):
    external_functions = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '60', 'rows': '4'}))
    external_contract = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '60', 'rows': '4'}))
    justification = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '60', 'rows': '4'}))

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('external_functions', 'external_contract', 'justification')


class MandatesArchivesForm(ModelForm):
    academic_year = forms.ModelChoiceField(queryset=academic_year.AcademicYear.objects.all(),
                                           widget=forms.Select(attrs={"onChange": 'submit()'}))

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('academic_year',)


class AssistantFormPart3(ModelForm):
    inscription = forms.ChoiceField(required=True, widget=forms.RadioSelect(renderer=HorizontalRadioRenderer, attrs={
        "onChange": 'Hide()'}), choices=mdl.academic_assistant.AcademicAssistant.PHD_INSCRIPTION_CHOICES)
    expected_phd_date = forms.DateField(required=False, widget=forms.DateInput(format='%d/%m/%Y',
                                                                               attrs={'placeholder': 'dd/mm/yyyy'}),
                                        input_formats=['%d/%m/%Y'])
    thesis_date = forms.DateField(required=False, widget=forms.DateInput(format='%d/%m/%Y',
                                                                         attrs={'placeholder': 'dd/mm/yyyy'}),
                                  input_formats=['%d/%m/%Y'])
    phd_inscription_date = forms.DateField(required=False, widget=forms.DateInput(format='%d/%m/%Y',
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
        fields = ('thesis_title', 'confirmation_test_date', 'remark', 'inscription',
                  'expected_phd_date', 'phd_inscription_date', 'confirmation_test_date', 'thesis_date'
                  )
        exclude = ['supervisor']


class AssistantFormPart4(ModelForm):
    internships = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '2'}))
    conferences = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '2'}))
    publications = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '2'}))
    awards = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '2'}))
    framing = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '2'}))
    remark = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '4'}))

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('internships', 'conferences', 'publications',
                  'awards', 'framing', 'remark')


class TutoringLearningUnitForm(forms.Form):
    sessions_number = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'input session_number'}))
    sessions_duration = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'input session_duration'}))
    series_number = forms.IntegerField(widget=forms.NumberInput(attrs={'class': 'input series_numbers'}))
    face_to_face_duration = forms.IntegerField(widget=forms.NumberInput(attrs={'readonly': 'enabled'}))
    attendees = forms.IntegerField(widget=forms.NumberInput(attrs={'min': '1', 'max': '999', 'step': '1'}))
    exams_supervision_duration = forms.IntegerField(
        widget=forms.NumberInput(attrs={'min': '1', 'max': '999', 'step': '1'}))
    others_delivery = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '4'}))
    mandate_id = forms.CharField(widget=forms.HiddenInput(), required=True)
    learning_unit_year = forms.CharField(required=True)
    tutoring_learning_unit_year_id = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super(TutoringLearningUnitForm, self).__init__(*args, **kwargs)
        self.fields['academic_year'] = \
            forms.ChoiceField(choices=[(obj.id, obj) for obj in academic_year.find_academic_years()])

    class Meta:
        model = mdl.tutoring_learning_unit_year.TutoringLearningUnitYear
        fields = ('academic_years', 'sessions_number', 'sessions_duration', 'series_numbers', 'face_to_face_duration',
                  'attendees', 'exams_supervision_duration', 'mandate', 'learning_unit_year')

    def clean(self):
        super(TutoringLearningUnitForm, self).clean()
        academic_year_id = self.cleaned_data.get("academic_year")
        learning_unit_acronym = self.cleaned_data.get('learning_unit_year')
        learning_units_year = learning_unit_year.search(academic_year_id=academic_year_id,
                                                        acronym=learning_unit_acronym)
        if not learning_units_year:
            msg = _("learning_unit_year_error_msg")
            self.add_error('learning_unit_year', msg)
        elif learning_units_year.count() > 1:
            msg = _("learning_unit_year_multiple_msg")
            self.add_error('learning_unit_year', msg)
            for this_learning_unit_year in learning_units_year:
                msg_acronym = this_learning_unit_year.acronym
                self.add_error('learning_unit_year', msg_acronym)

    def save(self):
        data = self.cleaned_data
        academic_year_id = data.get("academic_year")
        learning_unit_acronym = data.get("learning_unit_year")
        this_learning_unit_year = learning_unit_year.search(academic_year_id=academic_year_id,
                                                            acronym=learning_unit_acronym)[:1].get()
        mandate_id = data.get("mandate_id")
        sessions_number = data.get("sessions_number")
        sessions_duration = data.get("sessions_duration")
        series_number = data.get("series_number")
        face_to_face_duration = data.get("face_to_face_duration")
        attendees = data.get("attendees")
        exams_supervision_duration = data.get("exams_supervision_duration")
        others_delivery = data.get("others_delivery")
        tutoring_learning_unit_year_id = data.get("tutoring_learning_unit_year_id")
        mandate = mdl.assistant_mandate.find_mandate_by_id(mandate_id)
        if tutoring_learning_unit_year_id:
            tutoring_learning_unit_year = mdl.tutoring_learning_unit_year.find_by_id(tutoring_learning_unit_year_id)
            tutoring_learning_unit_year.sessions_number = sessions_number
            tutoring_learning_unit_year.sessions_duration = sessions_duration
            tutoring_learning_unit_year.series_number = series_number
            tutoring_learning_unit_year.face_to_face_duration = face_to_face_duration
            tutoring_learning_unit_year.attendees = attendees
            tutoring_learning_unit_year.exams_supervision_duration = exams_supervision_duration
            tutoring_learning_unit_year.others_delivery = others_delivery
            tutoring_learning_unit_year.mandate = mandate
            tutoring_learning_unit_year.learning_unit_year = this_learning_unit_year
        else:
            tutoring_learning_unit_year = mdl.tutoring_learning_unit_year.TutoringLearningUnitYear.objects.create(
                learning_unit_year=this_learning_unit_year, sessions_number=sessions_number,
                sessions_duration=sessions_duration, series_number=series_number,
                face_to_face_duration=face_to_face_duration, attendees=attendees,
                exams_supervision_duration=exams_supervision_duration, others_delivery=others_delivery,
                mandate=mandate)
        tutoring_learning_unit_year.save()


class AssistantFormPart5(ModelForm):
    degrees = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '4'}))
    formations = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '4'}))

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('faculty_representation', 'institute_representation', 'sector_representation',
                  'governing_body_representation', 'corsci_representation', 'students_service',
                  'infrastructure_mgmt_service', 'events_organisation_service', 'publishing_field_service',
                  'scientific_jury_service', 'degrees', 'formations')


class ReviewForm(ModelForm):
    justification = forms.CharField(help_text=_("justification_required_if_conditional"),
                                    required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '5'}))
    remark = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '5'}))
    confidential = forms.CharField(help_text=_("information_not_provided_to_assistant"),
                                   required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '5'}))
    advice = forms.ChoiceField(required=True, widget=forms.RadioSelect(renderer=HorizontalRadioRenderer, attrs={
        "onChange": 'Hide()'}), choices=review_advice_choices.REVIEW_ADVICE_CHOICES)
    reviewer = forms.ChoiceField(required=False)

    class Meta:
        model = mdl.review.Review
        fields = ('mandate', 'reviewer', 'advice', 'status', 'justification', 'remark', 'confidential', 'changed')
        widgets = {'mandate': forms.HiddenInput(), 'reviewer': forms.HiddenInput, 'status': forms.HiddenInput,
                   'changed': forms.HiddenInput}

    def clean(self):
        super(ReviewForm, self).clean()
        advice = self.cleaned_data.get("advice")
        justification = self.cleaned_data.get('justification')
        if advice == review_advice_choices.CONDITIONAL and not justification:
            msg = _("justification_required_if_conditional")
            self.add_error('justification', msg)


class AssistantFormPart6(ModelForm):
    activities_report_remark = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'cols': '80', 'rows': '4'}))

    class Meta:
        model = mdl.assistant_mandate.AssistantMandate
        fields = ('tutoring_percent', 'service_activities_percent', 'formation_activities_percent',
                  'research_percent', 'activities_report_remark')

    def clean(self):
        tutoring_percent = self.cleaned_data['tutoring_percent']
        service_activities_percent = self.cleaned_data['service_activities_percent']
        formation_activities_percent = self.cleaned_data['formation_activities_percent']
        research_percent = self.cleaned_data['research_percent']

        if tutoring_percent + service_activities_percent + formation_activities_percent + research_percent != 100:
            raise ValidationError(_('total_must_be_100_message'))
        else:
            return self.cleaned_data


class ReviewerDelegationForm(ModelForm):
    role = forms.CharField(widget=forms.HiddenInput(), required=True)
    structure = forms.ModelChoiceField(widget=forms.HiddenInput(), required=True,
                                       queryset=structure.Structure.objects.all())

    class Meta:
        model = mdl.reviewer.Reviewer
        fields = ('structure', 'role')
        exclude = ['person']
        widgets = {
            'structure': forms.HiddenInput()
        }


class ReviewerForm(ModelForm):
    role = forms.ChoiceField(required=True, choices=reviewer_role.ROLE_CHOICES)
    structure = forms.ModelChoiceField(required=True, queryset=(
        structure.find_by_type('INSTITUTE') | structure.find_by_type('FACULTY') |
        structure.find_by_type('SECTOR')).order_by('type', 'acronym'))

    class Meta:
        model = mdl.reviewer.Reviewer
        fields = ('structure', 'role')
        exclude = ['person']


class SettingsForm(ModelForm):
    starting_date = forms.DateField(required=True, widget=widgets.SelectDateWidget)
    ending_date = forms.DateField(required=True, widget=widgets.SelectDateWidget)

    class Meta:
        model = mdl.settings.Settings
        fields = ('starting_date', 'ending_date')
