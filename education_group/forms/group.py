##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import Dict

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

from base.business.event_perms import EventPermEducationGroupEdition
from base.forms.common import ValidationRuleMixin
from base.forms.utils.choice_field import BLANK_CHOICE
from base.models import campus
from base.models.academic_year import AcademicYear
from base.models.enums.constraint_type import ConstraintTypeEnum
from education_group.forms import fields
from rules_management.enums import GROUP_PGRM_ENCODING_PERIOD, GROUP_DAILY_MANAGEMENT
from rules_management.mixins import PermissionFieldMixin


class GroupForm(ValidationRuleMixin, PermissionFieldMixin, forms.Form):
    code = forms.CharField(max_length=15, label=_("Code"), required=False)
    academic_year = forms.ModelChoiceField(queryset=AcademicYear.objects.all(), label=_("Validity"), required=False)
    abbreviated_title = forms.CharField(max_length=40, label=_("Acronym/Short title"), required=False)
    title_fr = forms.CharField(max_length=240, label=_("Title in French"), required=False)
    title_en = forms.CharField(max_length=240, label=_("Title in English"), required=False)
    credits = forms.IntegerField(
        label=_("Credits"),
        required=False,
        widget=forms.TextInput
    )
    constraint_type = forms.ChoiceField(
        choices=BLANK_CHOICE + list(ConstraintTypeEnum.choices()),
        label=_("Type of constraint"),
        required=False,
    )
    min_constraint = forms.IntegerField(
        label=_("minimum constraint"),
        required=False,
        widget=forms.TextInput
    )
    max_constraint = forms.IntegerField(
        label=_("maximum constraint"),
        required=False,
        widget=forms.TextInput
    )
    management_entity = forms.CharField(required=False)  # TODO: Replace with select2 widget
    teaching_campus = fields.MainCampusChoiceField(
        queryset=None,
        label=_("Learning location"),
        required=False,
        to_field_name='name',
    )
    remark_fr = forms.CharField(widget=forms.Textarea, label=_("Remark"), required=False)
    remark_en = forms.CharField(widget=forms.Textarea, label=_("remark in english"), required=False)

    def __init__(self, *args, user: User, group_type: str, **kwargs):
        self.user = user
        self.group_type = group_type

        super().__init__(*args, **kwargs)

        self.__init_academic_year_field()
        self.__init_management_entity_field()
        self.__init_teaching_campus()

    def __init_academic_year_field(self):
        if self.user.person.is_faculty_manager:
            self.fields['academic_year'].queryset = EventPermEducationGroupEdition.get_academic_years()\
                .filter(year__gte=settings.YEAR_LIMIT_EDG_MODIFICATION)
        else:
            self.fields['academic_year'].queryset = self.fields['academic_year'].queryset.filter(
                year__gte=settings.YEAR_LIMIT_EDG_MODIFICATION
            )

    def __init_management_entity_field(self):
        self.fields['management_entity'] = fields.ManagementEntitiesChoiceField(
            person=self.user.person,
            initial=self.initial['management_entity'].pk if self.initial.get('management_entity') else None,
            disabled=self.fields['management_entity'].disabled,
        )

    def __init_teaching_campus(self):
        self.fields["teaching_campus"].initial = campus.LOUVAIN_LA_NEUVE_CAMPUS_NAME

    # ValidationRuleMixin
    def field_reference(self, field_name: str) -> str:
        return '.'.join(["GroupForm", self.group_type, field_name])

    # PermissionFieldMixin
    def get_context(self) -> str:
        is_edition_period_opened = EventPermEducationGroupEdition(raise_exception=False).is_open()
        return GROUP_PGRM_ENCODING_PERIOD if is_edition_period_opened else GROUP_DAILY_MANAGEMENT

    # PermissionFieldMixin
    def get_model_permission_filter_kwargs(self) -> Dict:
        return {'context': self.get_context()}

    def clean_academic_year(self):
        if self.cleaned_data['academic_year']:
            return self.cleaned_data['academic_year'].year
        return None

    def clean_teaching_campus(self):
        if self.cleaned_data['teaching_campus']:
            return {
                'name': self.cleaned_data['teaching_campus'].name,
                'organization_name': self.cleaned_data['teaching_campus'].organization.name,
            }
        return None


class GroupAttachForm(GroupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['academic_year'].disabled = True
        self.fields['academic_year'].required = False


class GroupUpdateForm(GroupForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['academic_year'].disabled = True
        self.fields['academic_year'].required = False
        self.fields['code'].disabled = True
        self.fields['code'].required = False
