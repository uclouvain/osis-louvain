##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from osis_common.models.osis_model_admin import OsisModelAdmin


class MandataryAdmin(OsisModelAdmin):
    list_display = ('mandate', 'person', 'start_date', 'end_date')

    raw_id_fields = ('mandate', 'person')
    search_fields = ['person__first_name', 'person__last_name']


class Mandatary(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    mandate = models.ForeignKey('Mandate')
    person = models.ForeignKey('Person')
    start_date = models.DateField(auto_now=False, auto_now_add=False)
    end_date = models.DateField(auto_now=False, auto_now_add=False)


def find_by_education_group_year(an_education_group_year):
    return Mandatary.objects.filter(mandate__education_group=an_education_group_year.education_group,
                                    start_date__lte=an_education_group_year.academic_year.start_date,
                                    end_date__gte=an_education_group_year.academic_year.end_date) \
        .order_by('mandate__function', 'person__last_name', 'person__first_name')


def find_by_education_group_year_function(an_education_group_year, a_function):
    return Mandatary.objects.filter(mandate__education_group=an_education_group_year.education_group,
                                    mandate__function=a_function,
                                    start_date__lte=an_education_group_year.academic_year.start_date,
                                    end_date__gte=an_education_group_year.academic_year.end_date) \
        .order_by('person__last_name', 'person__first_name')
