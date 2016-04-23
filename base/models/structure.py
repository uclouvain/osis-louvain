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
from django.core.exceptions import ObjectDoesNotExist


class StructureAdmin(admin.ModelAdmin):
    list_display = ('acronym', 'title', 'part_of', 'organization', 'type')
    fieldsets = ((None, {'fields': ('acronym', 'title', 'part_of', 'organization', 'type')}),)
    raw_id_fields = ('part_of', )
    search_fields = ['acronym']


ENTITY_TYPE = (('SECTOR', 'sector'),
               ('FACULTY', 'faculty'),
               ('INSTITUTE', 'institute'),
               ('POLE', 'pole'),
               ('DOCTORAL_COMMISSION', 'doctoral_commission'),
               ('PROGRAM_COMMISSION', 'program_commission'),
               ('LOGISTIC', 'logistic'),
               ('UNDEFINED', 'undefined'),
               ('RESEARCH_CENTER', 'research_center'),
               ('TECHNOLOGIC_PLATFORM', 'technologic_platform'))


class Structure(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True)
    acronym = models.CharField(max_length=15)
    title = models.CharField(max_length=255)
    organization = models.ForeignKey('Organization', null=True)
    part_of = models.ForeignKey('self', null=True, blank=True)
    type = models.CharField(max_length=30, blank=True, null=True, choices=ENTITY_TYPE)

    def children(self):
        return Structure.objects.filter(part_of=self.pk)

    def serializable_object(self):
        obj = {'name': self.acronym, 'children': []}
        for child in self.children():
            obj['children'].append(child.serializable_object())
        return obj

    def __str__(self):
        return u"%s - %s" % (self.acronym, self.title)


def find_structures():
    return Structure.objects.all().order_by('acronym')


def find_by_id(structure_id):
    return Structure.objects.get(pk=structure_id)


def search(acronym=None, title=None, type=None):
    queryset = Structure.objects

    if acronym:
        queryset = queryset.filter(acronym__iexact=acronym)

    if title:
        queryset = queryset.filter(title__icontains=title)

    if type:
        queryset = queryset.filter(type=type)

    return queryset


def find_children(self):
    return Structure.objects.filter(part_of=self).order_by('acronym')


def find_by_organization(organization):
    return Structure.objects.filter(organization=organization, part_of__isnull=True)


def find_by_type(type):
    return Structure.objects.filter(type__icontains=type)


def find_tree_by_organization(organization):
    structure = Structure.objects.filter(organization=organization)
    tags = []
    if structure:
        for t in Structure.objects.filter(part_of=structure):
            tags.append(t.serializable_object())
    return tags


def find_structure_hierarchy(struc):
    structure = Structure.objects.get(pk=struc.id)
    tags = []
    if structure:
        for t in Structure.objects.filter(part_of=structure):
            tags.append(t.serializable_object())
    return tags


def find_by_acronym(acronym):
    try:
        return Structure.objects.get(acronym__iexact=acronym.strip())
    except ObjectDoesNotExist:
        return None


def find_faculty(a_structure):

    if a_structure.type == 'FACULTY':
        return a_structure
    else:
        parent = a_structure.part_of
        if parent:
            if parent.type != 'FACULTY':
                find_faculty(parent)
            else:
                return parent
        return None

