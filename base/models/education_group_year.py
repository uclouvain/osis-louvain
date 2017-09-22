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
    diploma_printing_orientation, active_status, duration_unit
from base.models import offer_year_domain as mdl_offer_year_domain
from base.models import offer_year_entity as mdl_offer_year_entity
from base.models import entity_version as mdl_entity_version
from base.models.enums import offer_year_entity_type


class EducationGroupYearAdmin(admin.ModelAdmin):
    list_display = ('acronym', 'title', 'academic_year', 'education_group_type', 'changed')
    fieldsets = ((None, {'fields': ('academic_year', 'acronym', 'title', 'education_group_type', 'education_group',
                                    'active', 'partial_deliberation', 'admission_exam',
                                    'funding', 'funding_direction', 'funding_cud', 'funding_direction_cud',
                                    'academic_type', 'university_certificate', 'fee_type', 'enrollment_campus',
                                    'main_teaching_campus', 'dissertation', 'internship',
                                    'schedule_type', 'english_activities', 'other_language_activities',
                                    'other_campus_activities', 'professional_title', 'joint_diploma',
                                    'diploma_printing_orientation', 'diploma_printing_title',
                                    'inter_organization_information', 'inter_university_french_community',
                                    'inter_university_belgium', 'inter_university_abroad', 'primary_language',
                                    'keywords', 'duration', 'duration_unit', 'title_english', 'enrollment_enabled')}),)
    list_filter = ('academic_year', 'education_group_type')
    raw_id_fields = ('education_group_type', 'academic_year', 'education_group')
    search_fields = ['acronym']


class EducationGroupYear(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    acronym = models.CharField(max_length=15, db_index=True)
    title = models.CharField(max_length=255)
    title_english = models.CharField(max_length=240, blank=True, null=True)
    academic_year = models.ForeignKey('AcademicYear')
    education_group = models.ForeignKey('EducationGroup')
    education_group_type = models.ForeignKey('OfferType', blank=True, null=True)
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
    professional_title = models.CharField(max_length=320, blank=True, null=True)
    joint_diploma = models.BooleanField(default=False)
    diploma_printing_orientation = models.CharField(max_length=30, choices=diploma_printing_orientation.DIPLOMA_FOCUS, blank=True, null=True)
    diploma_printing_title = models.CharField(max_length=140, blank=True, null=True)
    inter_organization_information = models.CharField(max_length=320, blank=True, null=True)
    inter_university_french_community = models.BooleanField(default=False)
    inter_university_belgium = models.BooleanField(default=False)
    inter_university_abroad = models.BooleanField(default=False)
    primary_language = models.ForeignKey('reference.Language', blank=True, null=True)
    keywords = models.CharField(max_length=320, blank=True, null=True)
    duration = models.IntegerField(blank=True, null=True)
    duration_unit = models.CharField(max_length=40,
                                     choices=duration_unit.DurationUnits.choices(),
                                     default=duration_unit.DurationUnits.QUADRIMESTER,
                                     blank=True, null=True)
    enrollment_enabled = models.BooleanField(default=False)

    def __str__(self):
        return u"%s - %s" % (self.academic_year, self.acronym)

    @property
    def domains(self):
        domains = mdl_offer_year_domain.find_by_education_group_year(self)
        ch = ''
        for offer_yr_domain in domains:
            ch = "{}-{} ".format(offer_yr_domain.domain.decree, offer_yr_domain.domain.name)
        return ch

    @property
    def administration_entity(self):
        result = mdl_offer_year_entity.find_by_education_group_year_first(self, offer_year_entity_type.ENTITY_ADMINISTRATION)
        if result:
            ev = mdl_entity_version.get_last_version(result.entity)
            return ev
        return None

    @property
    def management_entity(self):
        result = mdl_offer_year_entity.find_by_education_group_year_first(self, offer_year_entity_type.ENTITY_MANAGEMENT)
        if result:
            ev = mdl_entity_version.get_last_version(result.entity)
            return ev
        return None


def find_by_id(an_id):
    try:
        return EducationGroupYear.objects.get(pk=an_id)
    except EducationGroupYear.DoesNotExist:
        return None


def search(academic_yr=None, acronym=None):
    out = None
    queryset = EducationGroupYear.objects

    if academic_yr:
        queryset = queryset.filter(academic_year=academic_yr)

    if acronym:
        queryset = queryset.filter(acronym__icontains=acronym)

    if academic_yr or acronym:
        out = queryset.order_by('acronym')

    return out
