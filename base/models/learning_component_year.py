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

from base.models.enums import learning_component_year_type


class LearningComponentYearAdmin(admin.ModelAdmin):
    list_display = ('learning_container_year', 'title', 'acronym', 'type', 'comment')
    fieldsets = ((None, {'fields': ('learning_container_year', 'title', 'acronym',
                                    'type', 'comment', 'planned_classes', 'hourly_volume_total',
                                    'hourly_volume_partial')}),)
    search_fields = ['acronym']


class LearningComponentYear(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    learning_container_year = models.ForeignKey('LearningContainerYear')
    title = models.CharField(max_length=255, blank=True, null=True)
    acronym = models.CharField(max_length=3, blank=True, null=True)
    type = models.CharField(max_length=30, choices=learning_component_year_type.LEARNING_COMPONENT_YEAR_TYPES,
                            blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    planned_classes = models.IntegerField(blank=True, null=True)
    hourly_volume_total = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    hourly_volume_partial = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    deleted = models.BooleanField(default=False)

    def __str__(self):
        return u"%s - %s" % (self.acronym, self.title)

    class Meta:
        permissions = (
            ("can_access_learningunitcomponentyear", "Can access learning unit component year"),
        )

    @property
    def hourly_volume_partial_q2(self):
        if self.hourly_volume_total:
            if self.hourly_volume_partial:
                q2 = self.hourly_volume_total - self.hourly_volume_partial
                if q2 <= 0:
                    return None
                else:
                    return q2
        return None

    @property
    def volumes(self):
        if self.hourly_volume_total is None or self.hourly_volume_total == 0:
            return {'hourly_volume': '?',
                    'quadrimester_volume': '?',
                    'vol_q1': '?',
                    'vol_q2': '?'}
        else:
            if self.hourly_volume_partial is None or self.hourly_volume_partial == 0:
                return {'hourly_volume': self.hourly_volume_total,
                        'quadrimester_volume': '?',
                        'vol_q1': '?',
                        'vol_q2': '?'}
            else:
                if self.hourly_volume_partial and self.hourly_volume_partial == -1:
                    return {'hourly_volume': self.hourly_volume_total,
                            'quadrimester_volume': 'Q1|2',
                            'vol_q1': '({})'.format(self.hourly_volume_total),
                            'vol_q2': '({})'.format(self.hourly_volume_total)}
                else:
                    if self.hourly_volume_partial and self.hourly_volume_partial != -1:
                        vol_q2 = self.hourly_volume_total - self.hourly_volume_partial
                        if vol_q2 == 0:
                            vol_q2 = '-'

                        if self.hourly_volume_partial == self.hourly_volume_total:
                            q_n = 'Q1'
                        else:
                            if self.hourly_volume_partial == 0:
                                q_n = 'Q2'
                            else:
                                q_n = 'Q1&2'
                        return {'hourly_volume': self.hourly_volume_total,
                                'quadrimester_volume': q_n,
                                'vol_q1': self.hourly_volume_partial,
                                'vol_q2': vol_q2}


def find_by_id(learning_component_year_id):
    return LearningComponentYear.objects.get(pk=learning_component_year_id)


def find_by_learning_container_year(a_learning_container_year):
    return LearningComponentYear.objects.filter(learning_container_year=a_learning_container_year)\
                                        .order_by('type', 'acronym')
