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
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.validators import MaxValueValidator, MinValueValidator


class AssistantMandate(models.Model):
    RENEWAL_TYPE_CHOICES = (
        ('NORMAL', _('Normal')),
        ('EXCEPTIONAL', _('Exceptional')))

    STATE_CHOICES = (
        ('DECLINED', _('Declined')),
        ('TO_DO', _('To do')),
        ('TRTS', _('Trts')),
        ('PHD_SUPERVISOR', _('PhD supervisor')),
        ('RESEARCH', _('Research')),
        ('SUPERVISION', _('Supervision')),
        ('VICE_RECTOR', _('Vice rector')),
        ('DONE', _('Done')))

    APPEAL_CHOICES = (
        ('NONE', _('N/A')),
        ('POSITIVE_APPEAL', _('Positive appeal')),
        ('NEGATIVE_APPEAL', _('Negative appeal')),
        ('APPEAL_IN_PROGRESS', _('Appeal in progress')),
        ('NO_APPEAL', _('No appeal')))

    ASSISTANT_TYPE_CHOICES = (
        ('ASSISTANT', _('Assistant')),
        ('TEACHING_ASSISTANT', _('Teaching assistant')))

    assistant = models.ForeignKey('AcademicAssistant')
    academic_year = models.ForeignKey('base.AcademicYear')
    fulltime_equivalent = models.DecimalField(max_digits=3, decimal_places=2)
    entry_date = models.DateField()
    end_date = models.DateField()
    position_id = models.CharField(max_length=12)
    sap_id = models.CharField(max_length=12)
    grade = models.CharField(max_length=3)
    assistant_type = models.CharField(
        max_length=20, choices=ASSISTANT_TYPE_CHOICES, default='ASSISTANT')
    scale = models.CharField(max_length=3)
    absences = models.TextField(null=True, blank=True)
    comment = models.TextField(null=True, blank=True)
    other_status = models.CharField(max_length=50, null=True, blank=True)
    renewal_type = models.CharField(
        max_length=12, choices=RENEWAL_TYPE_CHOICES, default='NORMAL')
    external_functions = models.TextField(null=True, blank=True)
    external_contract = models.CharField(max_length=255, null=True, blank=True)
    justification = models.TextField(null=True, blank=True)
    state = models.CharField(
        max_length=20, choices=STATE_CHOICES, default='TO_DO')
    tutoring_remark = models.TextField(null=True, blank=True)
    activities_report_remark = models.TextField(null=True, blank=True)
    research_percent = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    tutoring_percent = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    service_activities_percent = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    formation_activities_percent = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)], default=0)
    internships = models.TextField(null=True, blank=True)
    conferences = models.TextField(null=True, blank=True)
    publications = models.TextField(null=True, blank=True)
    awards = models.TextField(null=True, blank=True)
    framing = models.TextField(null=True, blank=True)
    remark = models.TextField(null=True, blank=True)
    degrees = models.TextField(null=True, blank=True)
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
    appeal = models.CharField(
        max_length=20, choices=APPEAL_CHOICES, default='NONE')
    special = models.BooleanField(default=False)
    contract_duration = models.CharField(max_length=30)
    contract_duration_fte = models.CharField(max_length=30)
    service_activities_remark = models.TextField(null=True, blank=True)


def find_mandate_by_assistant_for_academic_year(assistant, this_academic_year):
    return AssistantMandate.objects.filter(assistant=assistant, academic_year=this_academic_year)


def find_mandate_by_id(mandate_id):
    return AssistantMandate.objects.get(id=mandate_id)


def find_mandate_by_academic_assistant(assistant):
    return AssistantMandate.objects.get(assistant=assistant)
