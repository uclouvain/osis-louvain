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

from base.models.enums import learning_component_year_type, learning_container_year_types
from base.models import learning_class_year
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class LearningComponentYearAdmin(SerializableModelAdmin):
    list_display = ('learning_container_year', 'title', 'acronym', 'type', 'comment')
    fieldsets = ((None, {'fields': ('learning_container_year', 'title', 'acronym', 'volume_declared_vacant',
                                    'type', 'comment', 'planned_classes', 'hourly_volume_partial')}),)
    search_fields = ['acronym', 'learning_container_year__acronym']
    raw_id_fields = ('learning_container_year',)
    list_filter = ('learning_container_year__academic_year',)


class LearningComponentYear(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    learning_container_year = models.ForeignKey('LearningContainerYear')
    title = models.CharField(max_length=255, blank=True, null=True)
    acronym = models.CharField(max_length=4, blank=True, null=True)
    type = models.CharField(max_length=30, choices=learning_component_year_type.LEARNING_COMPONENT_YEAR_TYPES,
                            blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    planned_classes = models.IntegerField(blank=True, null=True)
    hourly_volume_partial = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    deleted = models.BooleanField(default=False)
    volume_declared_vacant = models.DecimalField(max_digits=6, decimal_places=1, blank=True, null=True)

    def __str__(self):
        return u"%s - %s - %s" % (self.acronym, self.learning_container_year.acronym, self.title)

    class Meta:
        permissions = (
            ("can_access_learningunitcomponentyear", "Can access learning unit component year"),
        )

    @property
    def type_letter_acronym(self):
        if self.learning_container_year.container_type == learning_container_year_types.COURSE:
            if self.type == learning_component_year_type.LECTURING or self.type == learning_component_year_type.PRACTICAL_EXERCISES:
                return self.acronym
            return None
        else:
            return {
                learning_container_year_types.INTERNSHIP: 'S',
                learning_container_year_types.DISSERTATION: 'D',
            }.get(self.learning_container_year.container_type)

    @property
    def real_classes(self):
        return len(learning_class_year.find_by_learning_component_year(self))


def find_by_id(learning_component_year_id):
    return LearningComponentYear.objects.get(pk=learning_component_year_id)


def find_by_learning_container_year(learning_container_year, with_classes=False):
    queryset = LearningComponentYear.objects.filter(learning_container_year=learning_container_year)\
                                        .order_by('type', 'acronym')
    if with_classes:
        queryset = queryset.prefetch_related(
             models.Prefetch('learningclassyear_set', to_attr="classes")
        )

    return queryset
