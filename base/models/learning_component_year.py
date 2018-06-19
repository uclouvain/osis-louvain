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
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _

from base.models import learning_class_year
from base.models.enums import learning_component_year_type, learning_container_year_types
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class LearningComponentYearAdmin(SerializableModelAdmin):
    list_display = ('learning_container_year', 'acronym', 'type', 'comment')
    search_fields = ['acronym', 'learning_container_year__acronym']
    list_filter = ('learning_container_year__academic_year',)


class LearningComponentYear(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    learning_container_year = models.ForeignKey('LearningContainerYear')
    acronym = models.CharField(max_length=4, blank=True, null=True)
    type = models.CharField(max_length=30, choices=learning_component_year_type.LEARNING_COMPONENT_YEAR_TYPES,
                            blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    planned_classes = models.IntegerField(blank=True, null=True, default=1)
    hourly_volume_total_annual = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                                     verbose_name=_("hourly volume total annual"))
    hourly_volume_partial_q1 = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                                   verbose_name=_("hourly volume partial q1"))
    hourly_volume_partial_q2 = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                                   verbose_name=_("hourly volume partial q2"))
    volume_declared_vacant = models.DecimalField(max_digits=6, decimal_places=1, blank=True, null=True,
                                                 verbose_name=_("volume declared vacant"))

    _warnings = None

    def __str__(self):
        return u"%s - %s" % (self.acronym, self.learning_container_year.acronym)

    class Meta:
        permissions = (
            ("can_access_learningunitcomponentyear", "Can access learning unit component year"),
        )

    @property
    def type_letter_acronym(self):
        if self.learning_container_year.container_type == learning_container_year_types.COURSE:
            if self.type in (learning_component_year_type.LECTURING, learning_component_year_type.PRACTICAL_EXERCISES):
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

    @property
    def warnings(self):
        if self._warnings is None:
            self._warnings = self._check_volumes_consistency()
        return self._warnings

    def _check_volumes_consistency(self):
        _warnings = []

        vol_global = self.entitycomponentyear_set.aggregate(Sum('repartition_volume'))['repartition_volume__sum'] or 0
        vol_total_annual = self.hourly_volume_total_annual or 0
        vol_q1 = self.hourly_volume_partial_q1 or 0
        vol_q2 = self.hourly_volume_partial_q2 or 0
        planned_classes = self.planned_classes or 0

        if vol_q1 + vol_q2 != vol_total_annual:
            _warnings.append("{} ({})".format(
                _('Volumes are inconsistent'), _('Vol_tot is not equal to vol_q1 + vol_q2')))
        if vol_total_annual * planned_classes != vol_global:
            _warnings.append("{} ({})".format(
                _('Volumes are inconsistent'), _('Vol_global is not equal to Vol_tot * planned_classes')))
        if self.planned_classes == 0:
            _warnings.append("{} ({})".format(_('Volumes are inconsistent'), _('planned classes cannot be 0')))
        return _warnings


def find_by_id(learning_component_year_id):
    return LearningComponentYear.objects.get(pk=learning_component_year_id)


def find_by_learning_container_year(learning_container_year, with_classes=False):
    queryset = LearningComponentYear.objects.filter(learning_container_year=learning_container_year) \
        .order_by('type', 'acronym')
    if with_classes:
        queryset = queryset.prefetch_related(
             models.Prefetch('learningclassyear_set', to_attr="classes")
        )

    return queryset
