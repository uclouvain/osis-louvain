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
from django.contrib import admin
from django.db import models
from base.models import offer
from . import adviser


class FacultyAdviserAdmin(admin.ModelAdmin):
    list_display = ('offer', 'adviser', 'get_adviser_type')
    raw_id_fields = ('adviser', 'offer')
    search_fields = ('uuid',
                     'adviser__person__last_name',
                     'adviser__person__first_name',
                     'offer__title')


class FacultyAdviser(models.Model):
    adviser = models.ForeignKey(adviser.Adviser)
    offer = models.ForeignKey(offer.Offer)

    def __str__(self):
        return self.offer.title

    def get_adviser_type(self):
        return self.adviser.type


def search_by_adviser(a_adviser):
    objects = FacultyAdviser.objects.filter(adviser=a_adviser)
    offers = [obj.offer for obj in list(objects)]
    return offers
