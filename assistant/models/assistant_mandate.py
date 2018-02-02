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
from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.contrib import admin
from assistant.models.enums import assistant_mandate_state, assistant_type, assistant_mandate_renewal
from assistant.models.enums import assistant_mandate_appeal

class AssistantMandateAdmin(admin.ModelAdmin):
    list_display = ('assistant', 'renewal_type', 'academic_year')
    raw_id_fields = ('assistant',)

class AssistantMandate(models.Model):

    assistant = models.ForeignKey('AcademicAssistant')
    academic_year = models.ForeignKey('base.AcademicYear')
    fulltime_equivalent = models.DecimalField(max_digits=3, decimal_places=2)
    entry_date = models.DateField()
    end_date = models.DateField()
    position_id = models.CharField(max_length=12)
    sap_id = models.CharField(max_length=12)
    assistant_type = models.CharField(max_length=20, choices=assistant_type.ASSISTANT_TYPES,
                                      default=assistant_type.ASSISTANT)
    scale = models.CharField(max_length=3)
    absences = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    other_status = models.CharField(max_length=50, null=True, blank=True)
    renewal_type = models.CharField(max_length=12, choices=assistant_mandate_renewal.ASSISTANT_MANDATE_RENEWAL_TYPES,
                                    default=assistant_mandate_renewal.NORMAL)
    external_functions = models.TextField(null=True, blank=True)
    external_contract = models.CharField(max_length=255, null=True, blank=True)
    justification = models.TextField(null=True, blank=True)
    state = models.CharField(max_length=20, choices=assistant_mandate_state.ASSISTANT_MANDATE_STATES,
                             default=assistant_mandate_state.TO_DO)
    tutoring_remark = models.TextField(null=True, blank=True)
    activities_report_remark = models.TextField(null=True, blank=True)
    research_percent = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    tutoring_percent = models.PositiveIntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    service_activities_percent = models.PositiveIntegerField(validators=[MinValueValidator(0),
                                                                         MaxValueValidator(100)], default=0)
    formation_activities_percent  = models.PositiveIntegerField(validators=[MinValueValidator(0),
                                                                            MaxValueValidator(100)], default=0)
    internships = models.TextField(null=True, blank=True)
    conferences = models.TextField(null=True, blank=True)
    publications = models.TextField(null=True, blank=True)
    awards = models.TextField(null=True, blank=True)
    framing = models.TextField(null=True, blank=True)
    remark = models.TextField(null=True, blank=True)
    formations = models.TextField(null=True, blank=True)
    faculty_representation = models.PositiveIntegerField(default=0)
    institute_representation = models.PositiveIntegerField(default=0)
    sector_representation = models.PositiveIntegerField(default=0)
    governing_body_representation = models.PositiveIntegerField(default=0)
    corsci_representation = models.PositiveIntegerField(default=0)
    students_service = models.PositiveIntegerField(default=0)
    infrastructure_mgmt_service = models.PositiveIntegerField(default=0)
    events_organisation_service = models.PositiveIntegerField(default=0)
    publishing_field_service = models.PositiveIntegerField(default=0)
    scientific_jury_service = models.PositiveIntegerField(default=0)
    appeal = models.CharField(max_length=20, choices=assistant_mandate_appeal.ASSISTANT_MANDATE_APPEALS,
                              default=assistant_mandate_appeal.NONE)
    special = models.BooleanField(default=False)
    contract_duration = models.CharField(max_length=30)
    contract_duration_fte = models.CharField(max_length=30)
    service_activities_remark = models.TextField(null=True, blank=True)


def find_mandate_by_assistant_for_academic_year(assistant, this_academic_year):
    return AssistantMandate.objects.get(assistant=assistant, academic_year=this_academic_year)


def find_mandate_by_id(mandate_id):
    try:
        return AssistantMandate.objects.get(id=mandate_id)
    except AssistantMandate.DoesNotExist:
        return None


def find_mandate_by_academic_assistant(assistant):
    return AssistantMandate.objects.filter(assistant=assistant).order_by('academic_year')


def find_by_academic_year(academic_year):
    return AssistantMandate.objects.filter(academic_year=academic_year).order_by('assistant__person__last_name')


def find_before_year_for_assistant(year, assistant):
    return AssistantMandate.objects.filter(academic_year__year__lt=year).filter(assistant=assistant)


def find_for_supervisor_for_academic_year(supervisor, academic_year):
    return AssistantMandate.objects.filter(assistant__supervisor=supervisor).filter(academic_year=academic_year)


def find_mandate(assistant, academic_year, contract_number):
    return AssistantMandate.objects.filter(academic_year=academic_year).filter(assistant = assistant).\
        filter(sap_id = contract_number)
