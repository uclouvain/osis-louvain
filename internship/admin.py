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
from django.contrib import admin
from .models import *


class InternshipOfferAdmin(admin.ModelAdmin):
    list_display = ('organization','learning_unit_year', 'title', 'maximum_enrollments')
    fieldsets = ((None, {'fields': ('organization','learning_unit_year', 'title', 'maximum_enrollments')}),)

admin.site.register(InternshipOffer, InternshipOfferAdmin)


class InternshipEnrollmentAdmin(admin.ModelAdmin):
    list_display = ('learning_unit_enrollment','internship_offer', 'start_date', 'end_date')
    fieldsets = ((None, {'fields': ('learning_unit_enrollment','internship_offer', 'start_date', 'end_date')}),)

admin.site.register(InternshipEnrollment, InternshipEnrollmentAdmin)


class InternshipMasterAdmin(admin.ModelAdmin):
    list_display = ('reference', 'organization', 'internship_offer', 'person', 'civility', 'type_mastery', 'speciality')
    fieldsets = ((None, {'fields': ('reference', 'organization', 'internship_offer', 'person', 'civility', 'type_mastery', 'speciality')}),)

admin.site.register(InternshipMaster, InternshipMasterAdmin)


class InternshipChoiceAdmin(admin.ModelAdmin):
    list_display = ('student', 'organization', 'learning_unit_year', 'choice')
    fieldsets = ((None, {'fields': ('student', 'organization', 'learning_unit_year', 'choice')}),)

admin.site.register(InternshipChoice, InternshipChoiceAdmin)

class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('name', 'acronym', 'reference', 'type')
    fieldsets = ((None, {'fields': ('name', 'acronym', 'reference', 'website', 'type')}),)
    search_fields = ['acronym']

admin.site.register(Organization, OrganizationAdmin)

class OrganizationAddressAdmin(admin.ModelAdmin):
    list_display = ('organization', 'label', 'location', 'postal_code', 'city', 'country')
    fieldsets = ((None, {'fields': ('organization', 'label', 'location', 'postal_code', 'city', 'country')}),)

admin.site.register(OrganizationAddress, OrganizationAddressAdmin)
