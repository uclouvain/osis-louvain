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
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from reversion.admin import VersionAdmin

from base.business.learning_container_year import get_learning_container_year_warnings
from base.models import learning_unit_year, entity_version
from base.models.enums import learning_unit_year_subtypes, entity_container_year_link_type
from base.models.enums import vacant_declaration_type
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY, ALLOCATION_ENTITY, \
    ADDITIONAL_REQUIREMENT_ENTITY_1, ADDITIONAL_REQUIREMENT_ENTITY_2
from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.learning_unit_year import LearningUnitYear
from education_group import publisher
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin

FIELDS_FOR_COMPARISON = ['team', 'is_vacant', 'type_declaration_vacant']


class LearningContainerYearAdmin(VersionAdmin, SerializableModelAdmin):
    list_display = ('learning_container', 'academic_year', 'container_type', 'acronym', 'common_title')
    search_fields = ['acronym']
    list_filter = ('academic_year', 'in_charge', 'is_vacant',)


class LearningContainerYear(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    academic_year = models.ForeignKey('AcademicYear', on_delete=models.PROTECT)
    learning_container = models.ForeignKey('LearningContainer', on_delete=models.CASCADE)

    container_type = models.CharField(
        verbose_name=_('Type'),
        db_index=True,
        max_length=20,
        choices=LearningContainerYearType.choices(),
    )

    common_title = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Common title'))
    common_title_english = models.CharField(max_length=250, blank=True, null=True,
                                            verbose_name=_('Common English title'))
    acronym = models.CharField(max_length=10)
    changed = models.DateTimeField(null=True, auto_now=True)
    team = models.BooleanField(default=False, verbose_name=_('Team management'))
    is_vacant = models.BooleanField(default=False, verbose_name=_('Vacant'))
    type_declaration_vacant = models.CharField(max_length=100, blank=True, null=True,
                                               verbose_name=_('Decision'),
                                               choices=vacant_declaration_type.DECLARATION_TYPE)
    in_charge = models.BooleanField(default=False)

    requirement_entity = models.ForeignKey(
        to="base.Entity",
        null=True, blank=False,
        related_name='requirement_entities',
        on_delete=models.PROTECT,
    )
    allocation_entity = models.ForeignKey(
        to="base.Entity",
        null=True, blank=True,
        related_name='allocation_entities',
        on_delete=models.PROTECT,
    )
    additional_entity_1 = models.ForeignKey(
        to="base.Entity",
        null=True, blank=True,
        related_name='additional_entities_1',
        on_delete=models.PROTECT,
    )
    additional_entity_2 = models.ForeignKey(
        to="base.Entity",
        null=True, blank=True,
        related_name='additional_entities_2',
        on_delete=models.PROTECT,
    )

    _warnings = None

    def __str__(self):
        return u"%s - %s" % (self.acronym, self.common_title)

    class Meta:
        unique_together = ("learning_container", "academic_year",)
        permissions = (
            ("can_access_learningcontaineryear", "Can access learning container year"),
        )

    @property
    def warnings(self):
        if self._warnings is None:
            self._warnings = get_learning_container_year_warnings(self)
        return self._warnings

    @cached_property
    def requirement_entity_version(self):
        return entity_version.find_entity_version_according_academic_year(
            self.requirement_entity, self.academic_year
        )

    @cached_property
    def allocation_entity_version(self):
        return entity_version.find_entity_version_according_academic_year(
            self.allocation_entity, self.academic_year
        )

    def get_partims_related(self):
        return learning_unit_year.search(learning_container_year_id=self,
                                         subtype=learning_unit_year_subtypes.PARTIM).order_by('acronym')

    def is_type_for_faculty(self) -> bool:
        return self.container_type in LearningContainerYearType.for_faculty()

    @staticmethod
    def get_attrs_by_entity_container_type():
        return {
            REQUIREMENT_ENTITY: 'requirement_entity',
            ALLOCATION_ENTITY: 'allocation_entity',
            ADDITIONAL_REQUIREMENT_ENTITY_1: 'additional_entity_1',
            ADDITIONAL_REQUIREMENT_ENTITY_2: 'additional_entity_2',
        }

    def get_entity_from_type(self, entity_container_type):
        attr = LearningContainerYear.get_attrs_by_entity_container_type()[entity_container_type]
        return getattr(self, attr, None)

    def get_map_entity_by_type(self) -> dict:
        return {
            link_type: self.get_entity_from_type(link_type)
            for link_type in LearningContainerYear.get_attrs_by_entity_container_type()
        }

    def set_entity(self, entity_container_type, new_entity):
        attr = LearningContainerYear.get_attrs_by_entity_container_type()[entity_container_type]
        setattr(self, attr, new_entity)

    def set_entities(self, entities_by_type_to_set):
        for link_type, new_entity in entities_by_type_to_set.items():
            self.set_entity(link_type, new_entity)

    def get_most_recent_entity_acronym(self, entity_container_type):
        entity = self.get_entity_from_type(entity_container_type)
        return entity.most_recent_acronym if entity else None


def find_last_entity_version_grouped_by_linktypes(learning_container_year, link_type=None):
    if link_type is None:
        link_types = entity_container_year_link_type.ENTITY_TYPE_LIST
    else:
        link_types = [link_type]
    return {
        link_type: entity.get_latest_entity_version()
        for link_type, entity in learning_container_year.get_map_entity_by_type().items()
        if entity and link_type in link_types
    }
