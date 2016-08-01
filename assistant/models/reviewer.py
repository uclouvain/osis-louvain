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
from base.models import structure
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from assistant.models import mandate_structure, assistant_mandate


class ReviewerAdmin(admin.ModelAdmin):
    list_display = ('person', 'structure', 'role')
    fieldsets = (
        (None, {'fields': ('person', 'structure', 'role')}),)
    raw_id_fields = ('person', )
    search_fields = ['person__first_name', 'person__last_name',
                     'person__global_id', 'structure__acronym']

    def get_form(self, request, obj=None, **kwargs):
        form = super(ReviewerAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['structure'].queryset = structure.Structure.objects.filter(
        Q(type='INSTITUTE') | Q(type='FACULTY') | Q(type='SECTOR') | Q(type='POLE') | Q(type='PROGRAM_COMMISSION'))
        return form

ROLE_CHOICES = (
    ('PHD_SUPERVISOR', _('phd_supervisor')),
    ('SUPERVISION', _('supervision')),
    ('SUPERVISION_ASSISTANT', _('supervision_assistant')),
    ('RESEARCH', _('research')),
    ('RESEARCH_ASSISTANT', _('research_assistant')),
    ('SECTOR_VICE_RECTOR', _('sector_vice_rector')),
    ('SECTOR_VICE_RECTOR_ASSISTANT', _('sector_vice_rector_assistant')))


class Reviewer(models.Model):
    person = models.ForeignKey('base.Person')
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    structure = models.ForeignKey('base.Structure', blank=True, null=True)

    def __str__(self):
        return u"%s - %s : %s" % (self.person, self.structure, self.role)

def find_by_id(reviewer_id):
    return Reviewer.objects.get(id=reviewer_id)

def find_by_person(person):
    return Reviewer.objects.get(person=person)

def canEditReview(reviewer_id, mandate_id):
    if assistant_mandate.find_mandate_by_id(mandate_id).state not in find_by_id(reviewer_id).role:
        return None
    if not mandate_structure.find_by_mandate_and_structure(
        assistant_mandate.find_mandate_by_id(mandate_id),find_by_id(reviewer_id).structure):
        return None
    else:
        return find_by_id(reviewer_id)
