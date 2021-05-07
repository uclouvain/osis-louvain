# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from typing import Dict, Optional

from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from base.forms.common import ValidationRuleMixin
from base.forms.utils import choice_field
from base.forms.utils.fields import OsisRichTextFormField
from base.models import campus
from base.models.academic_year import AcademicYear
from base.models.entity_version import EntityVersion
from base.models.enums import active_status, schedule_type as schedule_type_enum, education_group_categories, \
    education_group_types
from base.models.enums.constraint_type import ConstraintTypeEnum
from education_group.calendar.education_group_extended_daily_management import \
    EducationGroupExtendedDailyManagementCalendar
from education_group.calendar.education_group_preparation_calendar import EducationGroupPreparationCalendar
from education_group.forms import fields
from education_group.forms.fields import UpperCaseCharField
from rules_management.enums import MINI_TRAINING_PGRM_ENCODING_PERIOD, MINI_TRAINING_DAILY_MANAGEMENT
from rules_management.mixins import PermissionFieldMixin


class MiniTrainingForm(ValidationRuleMixin, forms.Form):
    code = UpperCaseCharField(max_length=15, label=_("Code"), required=False)
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label=_("Start"),
        to_field_name="year"
    )
    end_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label=_('Last year of organization'),
        required=False,
        to_field_name="year"
    )
    abbreviated_title = UpperCaseCharField(max_length=40, label=_("Acronym/Short title"), required=False)
    title_fr = forms.CharField(max_length=240, label=_("Title in French"))
    title_en = forms.CharField(max_length=240, label=_("Title in English"), required=False)
    keywords = forms.CharField(max_length=320, label=_('Keywords'), required=False)
    category = forms.ChoiceField(
        choices=education_group_categories.Categories.choices(),
        initial=education_group_categories.Categories.MINI_TRAINING.name,
        label=_('Category'),
        required=False,
        disabled=True
    )
    type = forms.ChoiceField(
        choices=education_group_types.MiniTrainingType.choices(),
        label=_('Type of training'),
        required=False,
        disabled=True
    )
    status = forms.ChoiceField(
        choices=active_status.ACTIVE_STATUS_LIST,
        initial=active_status.ACTIVE,
        label=_('Status')
    )
    schedule_type = forms.ChoiceField(
        choices=schedule_type_enum.SCHEDULE_TYPES,
        initial=schedule_type_enum.DAILY,
        label=_('Schedule type')
    )
    credits = fields.CreditField()
    constraint_type = forms.ChoiceField(
        choices=choice_field.add_blank(ConstraintTypeEnum.choices()),
        label=_("Type of constraint"),
        required=False,
    )
    min_constraint = forms.IntegerField(label=_("minimum constraint"), required=False)
    max_constraint = forms.IntegerField(label=_("maximum constraint"), required=False)
    management_entity = forms.CharField(required=False)  # TODO: Replace with select2 widget
    teaching_campus = fields.MainCampusChoiceField(
        queryset=None,
        label=_("Learning location"),
        to_field_name="name"
    )
    remark_fr = OsisRichTextFormField(config_name='link_only', label=_("Remark"), required=False)
    remark_en = OsisRichTextFormField(config_name='link_only', label=_("remark in english"), required=False)

    def __init__(self, *args, user: User, mini_training_type: str, attach_path: Optional[str], **kwargs):
        self.user = user
        self.group_type = mini_training_type
        self.attach_path = attach_path

        super().__init__(*args, **kwargs)

        self.__init_academic_year_field()
        self.__init_management_entity_field()
        self.__init_type_field()
        self.__init_teaching_campus()

    def __init_academic_year_field(self):
        if self.attach_path:
            self.fields['academic_year'].disabled = True

        target_years_opened = EducationGroupExtendedDailyManagementCalendar().get_target_years_opened()
        working_academic_years = AcademicYear.objects.filter(year__in=target_years_opened)
        self.fields['academic_year'].queryset = self.fields['end_year'].queryset = working_academic_years

        if not self.fields['academic_year'].disabled and self.user.person.is_faculty_manager:
            self.fields['academic_year'].queryset = self.fields['academic_year'].queryset.filter(
                year__in=EducationGroupPreparationCalendar().get_target_years_opened()
            )

        self.fields['end_year'].queryset = self.fields['end_year'].queryset.filter(
            year__gte=getattr(
                self.fields['academic_year'].queryset.first(), 'year', settings.YEAR_LIMIT_EDG_MODIFICATION
            )
        )

    def __init_management_entity_field(self):
        academic_year = self.initial.get('academic_year', None)
        if academic_year and not isinstance(academic_year, AcademicYear):
            academic_year = AcademicYear.objects.get(year=self.initial.get('academic_year'))
        self.fields['management_entity'] = fields.ManagementEntitiesModelChoiceField(
            person=self.user.person,
            initial=self.initial.get('management_entity'),
            disabled=self.fields['management_entity'].disabled,
            academic_year=academic_year
        )

    def __init_type_field(self):
        self.fields["type"].initial = self.group_type

    def __init_teaching_campus(self):
        self.fields["teaching_campus"].initial = campus.LOUVAIN_LA_NEUVE_CAMPUS_NAME

    # ValidationRuleMixin
    def field_reference(self, field_name: str) -> str:
        return '.'.join(["MiniTrainingForm", self.group_type, field_name])

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


class UpdateMiniTrainingForm(PermissionFieldMixin, MiniTrainingForm):
    abbreviated_title = UpperCaseCharField(
        max_length=40,
        label=_("Acronym/Short title"),
        required=True,
        disabled=True,
    )
    start_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label=_('Start academic year'),
        to_field_name="year",
        disabled=True,
        required=False
    )
    end_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label=_('Last year of organization'),
        required=False,
        to_field_name="year"
    )
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label=_("Validity"),
        required=False,
        disabled=True,
        to_field_name="year"
    )

    def __init__(self, *args, year=None, **kwargs):
        self.year = year
        super().__init__(*args, **kwargs)
        self.__init_end_year_field()
        self.__init_management_entity_field()

    def __init_end_year_field(self):
        initial_academic_year_value = self.initial.get("academic_year", None)
        if initial_academic_year_value:
            self.fields["end_year"].queryset = AcademicYear.objects.filter(
                year__gte=initial_academic_year_value,
                year__in=EducationGroupExtendedDailyManagementCalendar().get_target_years_opened()
            )

    def __init_management_entity_field(self):
        academic_year = AcademicYear.objects.get(year=self.year)
        old_entity = self.initial.get('management_entity', None)
        msg = EntityVersion.get_message_is_entity_active(old_entity, academic_year)
        self.fields['management_entity'] = fields.ManagementEntitiesModelChoiceField(
            person=self.user.person,
            initial=self.initial.get('management_entity'),
            disabled=self.fields['management_entity'].disabled,
            academic_year=academic_year,
            help_text=msg
        )

    # PermissionFieldMixin
    def get_context(self) -> str:
        is_edition_period_opened = EducationGroupPreparationCalendar().is_target_year_authorized(target_year=self.year)
        return MINI_TRAINING_PGRM_ENCODING_PERIOD if is_edition_period_opened else MINI_TRAINING_DAILY_MANAGEMENT

    # PermissionFieldMixin
    def get_model_permission_filter_kwargs(self) -> Dict:
        return {'context': self.get_context()}
