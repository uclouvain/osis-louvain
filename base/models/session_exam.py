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
from base.models.enums import number_session


class SessionExamAdmin(admin.ModelAdmin):
    list_display = ('offer_year', 'learning_unit_year', 'number_session', 'changed')
    list_filter = ('learning_unit_year__academic_year', 'number_session', 'offer_year__academic_year')
    raw_id_fields = ('learning_unit_year', 'offer_year')
    fieldsets = ((None, {'fields': ('learning_unit_year', 'number_session', 'offer_year')}),)
    search_fields = ['learning_unit_year__acronym', 'offer_year__acronym']


class SessionExam(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    number_session = models.IntegerField(choices=number_session.NUMBERS_SESSION)
    learning_unit_year = models.ForeignKey('LearningUnitYear')
    offer_year = models.ForeignKey('OfferYear', blank=True, null=True)
    progress = None

    def __str__(self):
        return u"%s - %d" % (self.learning_unit_year, self.number_session)
