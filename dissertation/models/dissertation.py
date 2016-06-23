##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
from dissertation.models import proposition_dissertation
from base.models import offer_year, student
from django.db.models import Q
from django.contrib import admin


class DissertationAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'active')


class Dissertation(models.Model):
    STATUS_CHOICES = (
        ('DRAFT', _('Draft')),
        ('DIR_SUBMIT', _('Submitted to Director')),
        ('DIR_OK', _('Accepted by Director')),
        ('DIR_KO', _('Refused by Director')),
        ('COM_SUBMIT', _('Submitted to Commission')),
        ('COM_OK', _('Accepted by Commission')),
        ('COM_KO', _('Refused by Commission')),
        ('EVA_SUBMIT', _('Submitted to First Year Evaluation')),
        ('EVA_OK', _('Accepted by First Year Evaluation')),
        ('EVA_KO', _('Refused by First Year Evaluation')),
        ('TO_RECEIVE', _('To be received')),
        ('TO_DEFEND', _('To be defended')),
        ('DEFENDED', _('Defended')),
        ('ENDED', _('Ended')),
        ('ENDED_WIN', _('Ended Win')),
        ('ENDED_LOS', _('Ended Los')),
    )

    title = models.CharField(max_length=200)
    author = models.ForeignKey(student.Student)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='DRAFT')
    offer_year_start = models.ForeignKey(offer_year.OfferYear)
    proposition_dissertation = models.ForeignKey(proposition_dissertation.PropositionDissertation)
    description = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    creation_date = models.DateTimeField(auto_now_add=True, editable=False)
    modification_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["author__person__last_name", "author__person__middle_name", "author__person__first_name", "title"]


def search_dissertation(terms=None):
    queryset = Dissertation.objects.all()
    if terms:
        queryset = queryset.filter(
            Q(author__person__first_name__icontains=terms) |
            Q(author__person__middle_name__icontains=terms) |
            Q(author__person__last_name__icontains=terms) |
            Q(description__icontains=terms) |
            Q(proposition_dissertation__title__icontains=terms) |
            Q(proposition_dissertation__author__person__first_name__icontains=terms) |
            Q(proposition_dissertation__author__person__middle_name__icontains=terms) |
            Q(proposition_dissertation__author__person__last_name__icontains=terms) |
            Q(status__icontains=terms) |
            Q(title__icontains=terms)
        ).distinct()
    return queryset
