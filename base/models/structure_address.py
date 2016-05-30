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
from django.contrib import admin


class StructureAddressAdmin(admin.ModelAdmin):
    list_display = ('structure', 'label', 'location', 'postal_code', 'city', 'country')
    fieldsets = ((None, {'fields': ('structure', 'label', 'location', 'postal_code', 'city', 'country', 'phone', 'fax', 'email')}),)
    search_fields = ['structure__acronym']


class StructureAddress(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    structure = models.ForeignKey('Structure')
    label = models.CharField(max_length=20)
    location = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=20)
    city = models.CharField(max_length=255)
    country = models.ForeignKey('reference.Country')
    phone = models.CharField(max_length=30, blank=True, null=True)
    fax = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)


def find_structure_address(a_structure):
    return StructureAddress.objects.filter(structure=a_structure).first()
