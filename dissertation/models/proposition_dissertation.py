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
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from dissertation.models import adviser, offer_proposition
from django.db.models import Q
from django.contrib import admin


class PropositionDissertationAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'visibility', 'active')


class PropositionDissertation(models.Model):
    TYPES_CHOICES = (
        ('RDL', _('Litterature review')),
        ('EDC', _('Case study')),
        )

    LEVELS_CHOICES = (
        ('DOMAIN', _('Domain')),
        ('WORK', _('Work')),
        ('QUESTION', _('Question')),
        ('THEME', _('Theme')),
        )

    COLLABORATION_CHOICES = (
        ('POSSIBLE', _('Possible')),
        ('REQUIRED', _('Required')),
        ('FORBIDDEN', _('Forbidden')),
        )

    author = models.ForeignKey(adviser.Adviser)
    collaboration = models.CharField(max_length=12, choices=COLLABORATION_CHOICES, default='FORBIDDEN')
    description = models.TextField(blank=True, null=True)
    level = models.CharField(max_length=12, choices=LEVELS_CHOICES, default='DOMAIN')
    max_number_student = models.IntegerField()
    title = models.CharField(max_length=200)
    type = models.CharField(max_length=12, choices=TYPES_CHOICES, default='RDL')
    visibility = models.BooleanField(default=True)
    active = models.BooleanField(default=True)
    offer_proposition = models.ManyToManyField(offer_proposition.OfferProposition)
    created_date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        first_name = ""
        middle_name = ""
        last_name = ""
        if self.author.person.first_name:
            first_name = self.author.person.first_name
        if self.author.person.middle_name:
            middle_name = self.author.person.middle_name
        if self.author.person.last_name:
            last_name = self.author.person.last_name + ","
        author = u"%s %s %s" % (last_name.upper(), first_name, middle_name)
        return author+" - "+str(self.title)

    class Meta:
        ordering = ["author__person__last_name", "author__person__middle_name", "author__person__first_name", "title"]


def search_proposition_dissertation(terms=None):
    queryset = PropositionDissertation.objects.all()
    if terms:
        queryset = queryset.filter(
            Q(title__icontains=terms) |
            Q(description__icontains=terms) |
            Q(author__person__first_name__icontains=terms) |
            Q(author__person__middle_name__icontains=terms) |
            Q(author__person__last_name__icontains=terms) |
            Q(offer_proposition__acronym__icontains=terms)
        ).distinct()
    return queryset
