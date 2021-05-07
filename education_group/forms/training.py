##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import functools
import operator
from typing import Dict, List, Union, Optional

from ajax_select import register, LookupChannel
from django import forms
from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q
from django.db.models import Value, CharField
from django.db.models.functions import Concat
from django.utils.functional import lazy
from django.utils.translation import gettext_lazy as _

from base.forms.common import ValidationRuleMixin
from base.forms.utils.choice_field import BLANK_CHOICE, add_blank
from base.forms.utils.fields import OsisRichTextFormField
from base.models import campus
from base.models.academic_year import AcademicYear
from base.models.certificate_aim import CertificateAim
from base.models.entity_version import EntityVersion
from base.models.enums.academic_type import AcademicTypes
from base.models.enums.active_status import ActiveStatusEnum
from base.models.enums.activity_presence import ActivityPresence
from base.models.enums.constraint_type import ConstraintTypeEnum
from base.models.enums.decree_category import DecreeCategories
from base.models.enums.duration_unit import DurationUnitsEnum
from base.models.enums.education_group_types import TrainingType
from base.models.enums.funding_codes import FundingCodes
from base.models.enums.internship_presence import InternshipPresence
from base.models.enums.rate_code import RateCode
from base.models.enums.schedule_type import ScheduleTypeEnum
from education_group.calendar.education_group_extended_daily_management import \
    EducationGroupExtendedDailyManagementCalendar
from education_group.calendar.education_group_preparation_calendar import EducationGroupPreparationCalendar
from education_group.ddd.business_types import *
from education_group.forms import fields
from education_group.forms.fields import MainEntitiesVersionChoiceField, UpperCaseCharField
from education_group.forms.widgets import CertificateAimsWidget
from osis_role.errors import get_permission_error
from reference.models.domain import Domain
from reference.models.domain_isced import DomainIsced
from reference.models.enums import domain_type
from reference.models.enums.domain_type import UNIVERSITY
from reference.models.language import Language, FR_CODE_LANGUAGE
from rules_management.enums import TRAINING_PGRM_ENCODING_PERIOD, \
    TRAINING_DAILY_MANAGEMENT
from rules_management.mixins import PermissionFieldMixin


def _get_section_choices():
    return add_blank(CertificateAim.objects.values_list('section', 'section').distinct().order_by('section'))


class CreateTrainingForm(ValidationRuleMixin, forms.Form):

    # panel_informations_form.html
    acronym = UpperCaseCharField(max_length=15, label=_("Acronym/Short title"))
    code = UpperCaseCharField(max_length=15, label=_("Code"))
    active = forms.ChoiceField(
        initial=ActiveStatusEnum.ACTIVE.name,
        choices=BLANK_CHOICE + list(ActiveStatusEnum.choices()),
        label=_("Status"),
    )
    schedule_type = forms.ChoiceField(
        initial=ScheduleTypeEnum.DAILY.name,
        choices=BLANK_CHOICE + list(ScheduleTypeEnum.choices()),
        label=_("Schedule type"),
    )
    credits = fields.CreditField()
    constraint_type = forms.ChoiceField(
        choices=BLANK_CHOICE + list(ConstraintTypeEnum.choices()),
        label=_("Type of constraint"),
        required=False,
    )
    min_constraint = forms.IntegerField(
        label=_("minimum constraint").capitalize(),
        required=False,
    )
    max_constraint = forms.IntegerField(
        label=_("maximum constraint").capitalize(),
        required=False,
    )
    title_fr = forms.CharField(max_length=240, label=_("Title in French"))
    title_en = forms.CharField(max_length=240, label=_("Title in English"), required=False)
    partial_title_fr = forms.CharField(max_length=240, label=_("Partial title in French"), required=False)
    partial_title_en = forms.CharField(max_length=240, label=_("Partial title in English"), required=False)
    keywords = forms.CharField(max_length=320, label=_('Keywords'), required=False)

    # panel_academic_informations_form.html
    academic_type = forms.ChoiceField(
        choices=BLANK_CHOICE + list(AcademicTypes.choices()),
        label=_("Academic type"),
        required=False,
    )
    duration = forms.IntegerField(
        initial=1,
        label=_("Duration"),
        min_value=1,
    )
    duration_unit = forms.ChoiceField(
        initial=DurationUnitsEnum.QUADRIMESTER.name,
        choices=BLANK_CHOICE + sorted(list(DurationUnitsEnum.choices()), key=lambda c: c[1]),
        label=_("duration unit").capitalize(),
        required=False,
    )
    internship_presence = forms.ChoiceField(
        initial=InternshipPresence.NO.name,
        choices=sorted(list(InternshipPresence.choices()), key=lambda c: c[1]),
        label=_("Internship"),
    )
    is_enrollment_enabled = forms.BooleanField(initial=False, label=_('Enrollment enabled'), required=False)
    has_online_re_registration = forms.BooleanField(initial=True, label=_('Web re-registration'), required=False)
    has_partial_deliberation = forms.BooleanField(initial=False, label=_('Partial deliberation'), required=False)
    has_admission_exam = forms.BooleanField(initial=False, label=_('Admission exam'), required=False)
    has_dissertation = forms.BooleanField(initial=False, label=_('dissertation').capitalize(), required=False)
    produce_university_certificate = forms.BooleanField(
        initial=False,
        label=_('University certificate'),
        required=False,
    )
    decree_category = forms.ChoiceField(
        choices=BLANK_CHOICE + sorted(list(DecreeCategories.choices()), key=lambda c: c[1]),
        label=_("Decree category"),
        required=False,
    )
    rate_code = forms.ChoiceField(
        choices=BLANK_CHOICE + sorted(list(RateCode.choices()), key=lambda c: c[1]),
        label=_("Rate code"),
        required=False,
    )
    main_language = forms.ModelChoiceField(
        queryset=Language.objects.all().order_by('name'),
        label=_('Primary language'),
        to_field_name="name",
        initial=FR_CODE_LANGUAGE
    )
    english_activities = forms.ChoiceField(
        choices=BLANK_CHOICE + list(ActivityPresence.choices()),
        label=_("activities in English").capitalize(),
        required=False,
    )
    other_language_activities = forms.ChoiceField(
        choices=BLANK_CHOICE + list(ActivityPresence.choices()),
        label=_("Other languages activities"),
        required=False,
    )
    main_domain = forms.ModelChoiceField(
        queryset=Domain.objects.filter(
            type=UNIVERSITY
        ).select_related(
            'decree'
        ).annotate(
            form_key=Concat(
                "decree__name", Value(" - "), "code",
                output_field=CharField()
            )
        ),
        label=_('main domain').capitalize(),
        required=False,
        to_field_name="form_key"
    )
    secondary_domains = fields.SecondaryDomainsField(
        'university_domains',
        required=False,
        label=_('secondary domains').capitalize(),
    )
    isced_domain = forms.ModelChoiceField(
        queryset=DomainIsced.objects.all(),
        required=False,
        to_field_name="code",
        label=_('ISCED domain'),
    )
    internal_comment = forms.CharField(
        max_length=500,
        label=_("comment (internal)").capitalize(),
        required=False,
        widget=forms.Textarea,
    )

    # panel_entities_form.html
    management_entity = forms.CharField()
    administration_entity = forms.CharField()

    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label=_('Start'),
        to_field_name="year",
    )
    end_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label=_('Last year of organization'),
        required=False,
        to_field_name="year"
    )
    teaching_campus = fields.MainCampusChoiceField(
        queryset=None,
        label=_("Learning location"),
        to_field_name="name"
    )
    enrollment_campus = fields.MainCampusChoiceField(
        queryset=None,
        label=_("Enrollment campus"),
        to_field_name="name"
    )
    other_campus_activities = forms.ChoiceField(
        choices=BLANK_CHOICE + list(ActivityPresence.choices()),
        label=_("Activities on other campus"),
        required=False,
    )

    # panel_funding_form.html
    can_be_funded = forms.BooleanField(initial=False, label=_('Funding'), required=False)
    funding_direction = forms.ChoiceField(
        choices=BLANK_CHOICE + list(FundingCodes.choices()),
        label=_("Funding direction"),
        required=False,
    )
    can_be_international_funded = forms.BooleanField(
        initial=False,
        label=_('Funding international cooperation CCD/CUD'),
        required=False
    )
    international_funding_orientation = forms.ChoiceField(
        choices=BLANK_CHOICE + list(FundingCodes.choices()),
        label=_("Funding international cooperation CCD/CUD direction"),
        required=False,
    )

    # panel_remarks_form.html
    remark_fr = OsisRichTextFormField(config_name='link_only', label=_("Remark"), required=False)
    remark_english = OsisRichTextFormField(
        config_name='link_only',
        label=_("remark in english").capitalize(),
        required=False
    )

    # HOPS panel
    ares_code = forms.IntegerField(
        label=_('ARES study code'),
        required=False,
        max_value=9999
    )
    ares_graca = forms.IntegerField(
        label=_('ARES-GRACA'),
        required=False,
        max_value=9999
    )
    ares_authorization = forms.IntegerField(
        label=_('ARES ability'),
        required=False,
        max_value=9999
    )
    code_inter_cfb = forms.CharField(max_length=8, label=_('Code co-graduation inter CfB'), required=False)
    coefficient = forms.DecimalField(
        max_digits=7,
        decimal_places=4,
        label=_('Co-graduation total coefficient'),
        required=False,
        validators=[MinValueValidator(1), MaxValueValidator(9999)],
    )

    # Diploma tab
    section = forms.ChoiceField(
        label=_('filter by section').capitalize() + ':',
        choices=lazy(_get_section_choices, list),
        required=False,
        disabled=True
    )
    leads_to_diploma = forms.BooleanField(
        initial=False,
        label=_('Leads to diploma/certificate'),
        required=False,
    )
    diploma_printing_title = forms.CharField(max_length=240, required=False, label=_('Diploma title'))
    professional_title = forms.CharField(max_length=320, required=False, label=_('Professionnal title'))
    certificate_aims = forms.ModelMultipleChoiceField(
        label=_('certificate aims').capitalize(),
        queryset=CertificateAim.objects.all(),
        required=False,
        to_field_name="code",
        widget=CertificateAimsWidget(
            url='certificate_aim_autocomplete',
            attrs={
                'data-html': True,
                'data-placeholder': _('Search...'),
                'data-width': '100%',
            },
            forward=['section'],
        )
    )

    def __init__(self, *args, user: User, training_type: str, attach_path: Optional[str],
                 training: 'Training' = None, **kwargs):
        self.user = user
        self.training_type = training_type
        self.attach_path = attach_path
        self.training = training

        super().__init__(*args, **kwargs)

        if self.attach_path:
            self.fields['academic_year'].disabled = True

        self.__init_academic_year_field()
        self.__init_management_entity_field()
        self.__init_administration_entity_field()
        self.__init_certificate_aims_field()
        self.__init_diploma_fields()
        self.__init_main_language()
        self.__init_campuses()
        self.__init_secondary_domains()

    def __init_academic_year_field(self):
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

    def __init_administration_entity_field(self):
        academic_year = self.initial.get('academic_year', None)
        if academic_year and not isinstance(academic_year, AcademicYear):
            academic_year = AcademicYear.objects.get(year=self.initial.get('academic_year'))
        self.fields['administration_entity'] = MainEntitiesVersionChoiceField(
            queryset=None,
            to_field_name="acronym",
            label=_('Administration entity'),
            academic_year=academic_year
        )

    def __init_certificate_aims_field(self):
        self.fields['certificate_aims'].disabled = True
        self.fields['section'].disabled = True

    def __init_diploma_fields(self):
        if self.training_type in TrainingType.with_diploma_values_set_initially_as_true():
            self.fields['leads_to_diploma'].initial = True
            self.fields['diploma_printing_title'].required = True
        else:
            self.fields['leads_to_diploma'].initial = False
            self.fields['diploma_printing_title'].required = False

    def __init_main_language(self):
        self.fields["main_language"].initial = Language.objects.all().get(code=FR_CODE_LANGUAGE)

    def __init_campuses(self):
        self.fields["teaching_campus"].initial = campus.LOUVAIN_LA_NEUVE_CAMPUS_NAME
        self.fields["enrollment_campus"].initial = campus.LOUVAIN_LA_NEUVE_CAMPUS_NAME

    def __init_secondary_domains(self):
        self.fields["secondary_domains"].widget.attrs['placeholder'] = _('Enter text to search')

    # ValidationRuleMixin
    def field_reference(self, field_name: str) -> str:
        return '.'.join(["TrainingForm", self.training_type, field_name])


class UpdateTrainingForm(PermissionFieldMixin, CreateTrainingForm):
    acronym = UpperCaseCharField(
        max_length=15,
        label=_("Acronym/Short title"),
        disabled=True,
    )
    start_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label=_('Start academic year'),
        to_field_name="year",
        disabled=True,
        required=False
    )
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        label=_("Validity"),
        required=False,
        disabled=True,
        to_field_name="year"
    )

    def __init__(self, *args, year: int = None, **kwargs):
        self.year = year

        super().__init__(*args, **kwargs)
        self.__init_end_year_field()
        self.__init_certificate_aims_field()
        self.__init_management_entity_field()
        self.__init_administration_entity_field()

    def __init_end_year_field(self):
        initial_academic_year_value = self.initial.get("academic_year", None)
        if initial_academic_year_value:
            self.fields["end_year"].queryset = AcademicYear.objects.filter(
                year__gte=initial_academic_year_value,
                year__in=EducationGroupExtendedDailyManagementCalendar().get_target_years_opened()
            )

    def __init_certificate_aims_field(self):
        perm = 'base.change_educationgroupcertificateaim'
        if self.user.has_perm(perm, obj=self.training):
            self.fields['certificate_aims'].disabled = False
            self.fields['section'].disabled = False
            self.fields['certificate_aims'].widget.attrs['title'] = _('Select one or multiple certificate aims')
        else:
            permission_error_msg = get_permission_error(self.user, perm)
            self.fields['certificate_aims'].disabled = True
            self.fields['section'].disabled = True
            self.fields['certificate_aims'].widget.attrs['title'] = permission_error_msg
            self.fields['certificate_aims'].widget.attrs['class'] = 'cursor-not-allowed'

    def __init_management_entity_field(self):
        academic_year = AcademicYear.objects.get(year=self.year)
        old_entity = self.initial.get('management_entity', None)
        msg = EntityVersion.get_message_is_entity_active(old_entity, self.year)
        self.fields['management_entity'] = fields.ManagementEntitiesModelChoiceField(
            person=self.user.person,
            initial=self.initial.get('management_entity'),
            disabled=self.fields['management_entity'].disabled,
            academic_year=academic_year,
            help_text=msg
        )

    def __init_administration_entity_field(self):
        academic_year = AcademicYear.objects.get(year=self.year)
        old_entity = self.initial.get('administration_entity', None)
        msg = EntityVersion.get_message_is_entity_active(old_entity, self.year)
        self.fields['administration_entity'] = MainEntitiesVersionChoiceField(
            queryset=None,
            to_field_name="acronym",
            label=_('Administration entity'),
            academic_year=academic_year,
            help_text=msg
        )

    # PermissionFieldMixin
    def get_context(self) -> str:
        is_edition_period_opened = EducationGroupPreparationCalendar().is_target_year_authorized(target_year=self.year)
        return TRAINING_PGRM_ENCODING_PERIOD if is_edition_period_opened else TRAINING_DAILY_MANAGEMENT

    # PermissionFieldMixin
    def get_model_permission_filter_kwargs(self) -> Dict:
        return {'context': self.get_context()}


@register('university_domains')
class UniversityDomainsLookup(LookupChannel):

    model = Domain

    def check_auth(self, request):
        if not request.user.is_authenticated:
            raise PermissionDenied

    def get_query(self, q, request):
        return self.model.objects.filter(type=domain_type.UNIVERSITY)\
                                 .filter(Q(name__icontains=q) | Q(code__icontains=q) |
                                         Q(decree__name__icontains=q))\
                                 .select_related('decree')\
                                 .order_by('-decree__name', 'name')

    def format_item_display(self, item):
        return "<span class='tag'>{}</span>".format(self.format_match(item))

    def get_result(self, item):
        return self.format_match(item)

    def format_match(self, item):
        return "{}:{} {}".format(item.decree.name, item.code, item.name)

    def get_objects(self, study_domains: Union[List['StudyDomain'], List[str]]):
        if not study_domains:
            return self.model.objects.none()

        if type(study_domains[0]) == str:
            return self.model.objects.filter(pk__in=study_domains)

        clauses = [Q(decree__name=study_domain.entity_id.decree_name, code=study_domain.entity_id.code)
                   for study_domain in study_domains]
        if not clauses:
            return self.model.objects.none()
        filter_clause = functools.reduce(operator.or_, clauses[1:], clauses[0])
        return self.model.objects.filter(filter_clause)
