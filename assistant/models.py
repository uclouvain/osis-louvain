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


class AcademicAssistant(models.Model):
    PHD_INSCRIPTION_CHOICES = (
        ('YES', _('Yes')),
        ('NO', _('No')),
        ('IN_PROGRESS', _('In progress')))
    
    person                 = models.ForeignKey('base.Person')
    supervisor             = models.ForeignKey('base.Person', blank=True, null=True, related_name='person_supervisor')
    position_id            = models.CharField(max_length=12)
    fulltime_equivalent    = models.DecimalField(max_digits=3, decimal_places=2)
    sap_id                 = models.CharField(max_length=12)
    entry_date             = models.DateField()
    end_date               = models.DateField()
    scale                  = models.CharField(max_length=3)
    thesis_title           = models.CharField(max_length=255, null=True, blank=True)
    phd_inscription_date   = models.DateField(null=True, blank=True)
    confirmation_test_date = models.DateField(null=True, blank=True)
    thesis_date            = models.DateField(null=True, blank=True)
    expected_phd_date      = models.DateField(null=True, blank=True)
    remark                 = models.TextField(null=True, blank=True)
    inscription            = models.CharField(max_length=12, choices=PHD_INSCRIPTION_CHOICES, default='YES')
    

class AssistantMandate(models.Model):
    RENEWAL_TYPE_CHOICES = (
        ('NORMAL', _('Normal')),
        ('EXCEPTIONAL', _('Exceptional')))
    
    STATE_CHOICES = (
        ('TO_DO', _('To do')),
        ('TRTS', _('Trts')),
        ('PHD_SUPERVISOR', _('PhD supervisor')),
        ('RESEARCH', _('Research')),
        ('SUPERVISION', _('Supervision')),
        ('VICE_RECTOR', _('Vice rector')))
    
    APPEAL_CHOICES = (
        ('NONE', _('N/A')),
        ('POSITIVE_APPEAL', _('Positive appeal')),
        ('NEGATIVE_APPEAL', _('Negative appeal')),
        ('APPEAL_IN_PROGRESS', _('Appeal in progress')),
        ('NO_APPEAL', _('No appeal')))
    
    assistant                     = models.ForeignKey(AcademicAssistant)
    absences                      = models.TextField(null=True, blank=True)
    comment                       = models.TextField(null=True, blank=True)
    other_status                  = models.CharField(max_length=50, null=True, blank=True)
    renewal_type                  = models.CharField(max_length=12, choices=RENEWAL_TYPE_CHOICES, default='NORMAL')
    external_functions            = models.TextField(null=True, blank=True)
    external_contract             = models.CharField(max_length=255, null=True, blank=True)
    justification                 = models.TextField(null=True, blank=True)
    state                         = models.CharField(max_length=20, choices=STATE_CHOICES, default='TO_DO')
    tutoring_remark               = models.TextField(null=True, blank=True)
    activities_report_remark      = models.TextField(null=True, blank=True)
    research_percent              = models.PositiveIntegerField(validators=[MinValueValidator(0),
                                                                            MaxValueValidator(100)], default=0)
    tutoring_percent              = models.PositiveIntegerField(validators=[MinValueValidator(0),
                                                                            MaxValueValidator(100)], default=0)
    service_activities_percent    = models.PositiveIntegerField(validators=[MinValueValidator(0),
                                                                            MaxValueValidator(100)], default=0)
    formation_activities_percent  = models.PositiveIntegerField(validators=[MinValueValidator(0),
                                                                            MaxValueValidator(100)], default=0)
    internships                   = models.TextField(null=True, blank=True)
    conferences                   = models.TextField(null=True, blank=True)
    publications                  = models.TextField(null=True, blank=True)
    awards                        = models.TextField(null=True, blank=True)
    framing                       = models.TextField(null=True, blank=True)
    remark                        = models.TextField(null=True, blank=True)
    degrees                       = models.TextField(null=True, blank=True)
    formations                    = models.TextField(null=True, blank=True)
    faculty_representation        = models.PositiveIntegerField(default=0)
    institute_representation      = models.PositiveIntegerField(default=0)
    sector_representation         = models.PositiveIntegerField(default=0)
    governing_body_representation = models.PositiveIntegerField(default=0)
    corsci_representation         = models.PositiveIntegerField(default=0)
    students_service              = models.PositiveIntegerField(default=0)
    infrastructure_mgmt_service   = models.PositiveIntegerField(default=0)
    events_organisation_service   = models.PositiveIntegerField(default=0)
    publishing_field_service      = models.PositiveIntegerField(default=0)
    scientific_jury_service       = models.PositiveIntegerField(default=0)
    appeal                        = models.CharField(max_length=20, choices=APPEAL_CHOICES, default='NONE')
    special                       = models.BooleanField(default=False)
    contract_duration             = models.CharField(max_length=30) 
    contract_duration_fte         = models.CharField(max_length=30)
    

class AssistantDocument(models.Model):
    DOC_TYPE_CHOICES = (
        ('PHD', _('PhD')),
        ('TUTORING', _('Tutoring')),
        ('RESEARCH', _('Research')))
    
    assistant = models.ForeignKey(AcademicAssistant)
    mandate = models.ForeignKey(AssistantMandate)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES)
    

class TutoringLearningUnitYear(models.Model):
    mandate                    = models.ForeignKey(AssistantMandate)
    sessions_duration          = models.PositiveIntegerField(null=True, blank=True)
    sessions_number            = models.PositiveIntegerField(null=True, blank=True)
    series_number              = models.PositiveIntegerField(null=True, blank=True)
    face_to_face_duration      = models.PositiveIntegerField(null=True, blank=True)
    attendees                  = models.PositiveIntegerField(null=True, blank=True)
    preparation_duration       = models.PositiveIntegerField(null=True, blank=True)
    exams_supervision_duration = models.PositiveIntegerField(null=True, blank=True)

    
class Review(models.Model):
    ADVICE_CHOICES = (
        ('FAVORABLE', _('Favorable')),
        ('CONDITIONAL', _('Conditional')),
        ('UNFAVOURABLE', _('Unfavourable')))
    
    mandate       = models.ForeignKey(AssistantMandate)
    advice        = models.CharField(max_length=20, choices=ADVICE_CHOICES)
    justification = models.TextField(null=True, blank=True)
    remark        = models.TextField(null=True, blank=True)
    confidential  = models.TextField(null=True, blank=True)

