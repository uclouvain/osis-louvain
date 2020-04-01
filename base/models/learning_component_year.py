##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from base.business.learning_units.quadrimester_strategy import LearningComponentYearQ1Strategy, \
    LearningComponentYearQ2Strategy, LearningComponentYearQ1and2Strategy, LearningComponentYearQ1or2Strategy, \
    LearningComponentYearQuadriNoStrategy
from base.models.enums import learning_component_year_type, learning_container_year_types, quadrimesters
from base.models.enums.component_type import LECTURING, PRACTICAL_EXERCISES
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY, ADDITIONAL_REQUIREMENT_ENTITY_2, \
    ADDITIONAL_REQUIREMENT_ENTITY_1
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class LearningComponentYearAdmin(VersionAdmin, SerializableModelAdmin):
    list_display = ('learning_unit_year', 'acronym', 'type', 'comment', 'changed')
    search_fields = ['acronym', 'learning_unit_year__acronym']
    list_filter = ('learning_unit_year__academic_year',)


class RepartitionVolumeField(models.DecimalField):
    def __init__(self, *args, **kwargs):
        super(RepartitionVolumeField, self).__init__(*args, **kwargs)
        self.blank = self.null = True
        self.max_digits = 6
        self.decimal_places = 2


class LearningComponentYear(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    learning_unit_year = models.ForeignKey('LearningUnitYear', on_delete=models.CASCADE)
    acronym = models.CharField(max_length=4, blank=True, null=True)
    type = models.CharField(max_length=30, choices=learning_component_year_type.LEARNING_COMPONENT_YEAR_TYPES,
                            blank=True, null=True)
    comment = models.CharField(max_length=255, blank=True, null=True)
    planned_classes = models.IntegerField(blank=True, null=True)
    hourly_volume_total_annual = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                                     verbose_name=_("hourly volume total annual"))
    hourly_volume_partial_q1 = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                                   verbose_name=_("hourly volume partial q1"))
    hourly_volume_partial_q2 = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True,
                                                   verbose_name=_("hourly volume partial q2"))
    volume_declared_vacant = models.DecimalField(max_digits=6, decimal_places=1, blank=True, null=True,
                                                 verbose_name=_("volume declared vacant"))
    repartition_volume_requirement_entity = RepartitionVolumeField()
    repartition_volume_additional_entity_1 = RepartitionVolumeField()
    repartition_volume_additional_entity_2 = RepartitionVolumeField()

    _warnings = None

    def __str__(self):
        return "{} - {}".format(self.acronym, self.learning_unit_year.acronym)

    class Meta:
        permissions = (
            ("can_access_learningunitcomponentyear", "Can access learning unit component year"),
        )

    @property
    def type_letter_acronym(self):
        if self.learning_unit_year.learning_container_year.container_type == learning_container_year_types.COURSE:
            if self.type in (learning_component_year_type.LECTURING, learning_component_year_type.PRACTICAL_EXERCISES):
                return self.acronym
            return None
        else:
            return {
                learning_container_year_types.INTERNSHIP: 'S',
                learning_container_year_types.DISSERTATION: 'D',
            }.get(self.learning_unit_year.learning_container_year.container_type)

    @property
    def complete_acronym(self):
        # FIXME :: Temporary solution - waiting for business clarification about "components" concept (untyped, ...)
        if self.acronym == 'NT':
            return '{}/PM'.format(self.learning_unit_year.acronym)
        else:
            return '{}/{}'.format(self.learning_unit_year.acronym, self.acronym)

    @cached_property
    def real_classes(self) -> int:
        # FIXME :: Temporary solution - Waiting for real classes in OSIS
        real_classes = self.learningclassyear_set.count()
        if self.planned_classes and self.planned_classes > 0 and real_classes == 0:
            return 1
        return real_classes

    @property
    def warnings(self):
        if self._warnings is None:
            self._warnings = self._check_volumes_consistency()
        return self._warnings

    def _check_volumes_consistency(self):
        _warnings = []

        vol_total_annual = self.hourly_volume_total_annual or 0
        vol_q1 = self.hourly_volume_partial_q1 or 0
        vol_q2 = self.hourly_volume_partial_q2 or 0
        planned_classes = self.planned_classes or 0
        inconsistent_msg = _('Volumes of {} are inconsistent').format(self.complete_acronym)
        if vol_q1 + vol_q2 != vol_total_annual:
            _warnings.append("{} ({})".format(
                inconsistent_msg,
                _('The annual volume must be equal to the sum of the volumes Q1 and Q2')))
        if self.vol_global != sum([value or Decimal(0) for value in self.repartition_volumes.values()]):
            _warnings.append("{} ({})".format(
                inconsistent_msg,
                _('the sum of repartition volumes must be equal to the global volume')))
        if planned_classes == 0 and vol_total_annual > 0:
            _warnings.append("{} ({})".format(
                inconsistent_msg,
                _('planned classes cannot be 0 while volume is greater than 0')))
        if planned_classes > 0 and vol_total_annual == 0:
            _warnings.append("{} ({})".format(
                inconsistent_msg,
                _('planned classes cannot be greather than 0 while volume is equal to 0')))

        strategies = {
            None: LearningComponentYearQuadriNoStrategy,
            quadrimesters.LearningUnitYearQuadrimester.Q1.name: LearningComponentYearQ1Strategy,
            quadrimesters.LearningUnitYearQuadrimester.Q2.name: LearningComponentYearQ2Strategy,
            quadrimesters.LearningUnitYearQuadrimester.Q1and2.name: LearningComponentYearQ1and2Strategy,
            quadrimesters.LearningUnitYearQuadrimester.Q1or2.name: LearningComponentYearQ1or2Strategy,
            quadrimesters.LearningUnitYearQuadrimester.Q3.name: LearningComponentYearQuadriNoStrategy,
        }

        try:
            strategies[self.learning_unit_year.quadrimester](lcy=self).is_valid()
        except ValidationError as e:
            _warnings.append("{} ({})".format(inconsistent_msg, e.message))

        return _warnings

    @cached_property
    def vol_global(self):
        return (self.hourly_volume_total_annual or Decimal(0)) * (self.planned_classes or Decimal(0))

    @property
    def repartition_volumes(self):
        return {
            REQUIREMENT_ENTITY: self.repartition_volume_requirement_entity,
            ADDITIONAL_REQUIREMENT_ENTITY_1: self.repartition_volume_additional_entity_1,
            ADDITIONAL_REQUIREMENT_ENTITY_2: self.repartition_volume_additional_entity_2,
        }

    def set_repartition_volume(self, entity_container_type, repartition_volume):
        attr_name = self.repartition_volume_attrs_by_entity_container_type()[entity_container_type]
        setattr(self, attr_name, repartition_volume)

    @staticmethod
    def repartition_volume_attrs_by_entity_container_type():
        return {
            REQUIREMENT_ENTITY: 'repartition_volume_requirement_entity',
            ADDITIONAL_REQUIREMENT_ENTITY_1: 'repartition_volume_additional_entity_1',
            ADDITIONAL_REQUIREMENT_ENTITY_2: 'repartition_volume_additional_entity_2',
        }

    def set_repartition_volumes(self, repartition_volumes):
        for entity_container_type, attr in self.repartition_volume_attrs_by_entity_container_type().items():
            setattr(self, attr, repartition_volumes[entity_container_type])


def volume_total_verbose(learning_component_years):
    q1 = next((component['total'] for component in learning_component_years
               if component['type'] == LECTURING), 0)
    q2 = next((component['total'] for component in learning_component_years
               if component['type'] == PRACTICAL_EXERCISES), 0)
    return "%(q1)gh + %(q2)gh" % {"q1": q1, "q2": q2}


def find_by_id(learning_component_year_id):
    return LearningComponentYear.objects.get(pk=learning_component_year_id)


def find_by_learning_container_year(learning_container_year, with_classes=False):
    queryset = LearningComponentYear.objects.filter(
        learning_unit_year__learning_container_year=learning_container_year
    ).order_by('type', 'acronym')
    if with_classes:
        queryset = queryset.prefetch_related(
            models.Prefetch('learningclassyear_set', to_attr="classes")
        )

    return queryset
