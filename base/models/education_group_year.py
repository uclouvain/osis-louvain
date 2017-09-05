##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib import admin
from base.models.enums import academic_type, fee, internship_presence, schedule_type, activity_presence, \
    diploma_printing_orientation, active_status


class EducationGroupYearAdmin(admin.ModelAdmin):
    list_display = ('acronym', 'title', 'academic_year', 'education_group_type', 'changed')
    fieldsets = ((None, {'fields': ('academic_year', 'acronym', 'title', 'education_group_type', 'education_group',
                                    'start_year', 'end_year', 'active', 'partial_deliberation', 'admission_exam',
                                    'funding', 'funding_direction', 'funding_cud', 'funding_direction_cud',
                                    'academic_type', 'university_certificate', 'fee_type', 'enrollment_campus',
                                    'main_teaching_campus', 'dissertation', 'internship',
                                    'schedule_type', 'english_activities', 'other_language_activities',
                                    'other_campus_activities', 'professionnal_title', 'joint_diploma',
                                    'diploma_printing_orientation', 'diploma_printing_title', 'inter_organization_information')}),)
    list_filter = ('academic_year', 'education_group_type')
    raw_id_fields = ('education_group_type', 'academic_year', 'education_group')
    search_fields = ['acronym']


class EducationGroupYear(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    acronym = models.CharField(max_length=15, db_index=True)
    title = models.CharField(max_length=255)
    academic_year = models.ForeignKey('AcademicYear')
    education_group = models.ForeignKey('EducationGroup')
    education_group_type = models.ForeignKey('OfferType', blank=True, null=True)
    start_year = models.IntegerField(blank=True, null=True)
    end_year = models.IntegerField(blank=True, null=True)
    active = models.CharField(max_length=20, choices=active_status.ACTIVE_STATUS_LIST, default=active_status.ACTIVE)
    partial_deliberation = models.BooleanField(default=False)
    admission_exam = models.BooleanField(default=False)
    funding = models.BooleanField(default=False)
    funding_direction = models.CharField(max_length=1, blank=True, null=True)
    funding_cud = models.BooleanField(default=False)  #cud = commission universitaire au développement
    funding_direction_cud = models.CharField(max_length=1, blank=True, null=True)
    academic_type = models.CharField(max_length=20, choices=academic_type.ACADEMIC_TYPES, blank=True, null=True)
    university_certificate = models.BooleanField(default=False)
    fee_type = models.CharField(max_length=20, choices=fee.FEES, blank=True, null=True)
    enrollment_campus = models.ForeignKey('Campus', related_name='enrollment', blank=True, null=True)
    main_teaching_campus = models.ForeignKey('Campus', blank=True, null=True, related_name='teaching')
    dissertation = models.BooleanField(default=False)
    internship = models.CharField(max_length=20, choices=internship_presence.INTERNSHIP_PRESENCE, blank=True, null=True)
    schedule_type = models.CharField(max_length=20, choices=schedule_type.SCHEDULE_TYPES, default=schedule_type.DAILY)
    english_activities = models.CharField(max_length=20, choices=activity_presence.ACTIVITY_PRESENCES, blank=True, null=True)
    other_language_activities = models.CharField(max_length=20, choices=activity_presence.ACTIVITY_PRESENCES, blank=True, null=True)
    other_campus_activities = models.CharField(max_length=20, choices=activity_presence.ACTIVITY_PRESENCES, blank=True, null=True)
    professionnal_title = models.CharField(max_length=320, blank=True, null=True)
    joint_diploma = models.BooleanField(default=False)
    diploma_printing_orientation = models.CharField(max_length=30, choices=diploma_printing_orientation.DIPLOMA_FOCUS, blank=True, null=True)
    diploma_printing_title = models.CharField(max_length=140, blank=True, null=True)
    inter_organization_information = models.CharField(max_length=320, blank=True, null=True)

    def __str__(self):
        return u"%s - %s" % (self.academic_year, self.acronym)
