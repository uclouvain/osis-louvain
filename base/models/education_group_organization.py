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
from base.models.enums import diploma_coorganization


class EducationGroupOrganizationAdmin(admin.ModelAdmin):
    list_display = ('education_group_year', 'organization')
    fieldsets = ((None, {'fields': ('education_group_year',
                                    'organization',
                                    'all_students',
                                    'enrollment_place',
                                    'diploma')}),)
    raw_id_fields = ('education_group_year', 'organization')
    search_fields = ['education_group_year']


class EducationGroupOrganization(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    education_group_year = models.ForeignKey('EducationGroupYear')
    organization = models.ForeignKey('Organization')
    all_students = models.BooleanField(default=False)
    enrollment_place = models.BooleanField(default=False)
    diploma = models.CharField(max_length=40,
                               choices=diploma_coorganization.DiplomaCoorganizationTypes.choices(),
                               default=diploma_coorganization.DiplomaCoorganizationTypes.NOT_CONCERNED)

def search(education_group_year):
    if education_group_year:
        return EducationGroupOrganization.objects.filter(education_group_year=education_group_year)
    return None
