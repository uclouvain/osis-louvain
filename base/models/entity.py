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
from django.db.models import Case, When, Q, F
from django.utils import timezone
from django.utils.functional import cached_property

from base.models.enums import entity_type
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin
from osis_common.utils.models import get_object_or_none


class EntityAdmin(SerializableModelAdmin):
    list_display = ('most_recent_acronym', 'external_id', 'organization', 'location', 'postal_code', 'phone')
    search_fields = ['external_id', 'entityversion__acronym', 'entityversion__title', 'organization__name']
    readonly_fields = ('organization', 'external_id')


class Entity(SerializableModel):
    organization = models.ForeignKey('Organization', blank=True, null=True, on_delete=models.CASCADE)
    external_id = models.CharField(max_length=255, unique=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)

    location = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.ForeignKey('reference.Country', blank=True, null=True, on_delete=models.PROTECT)
    phone = models.CharField(max_length=30, blank=True, null=True)
    fax = models.CharField(max_length=255, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return "{0}".format(self.most_recent_acronym)

    @cached_property
    def most_recent_acronym(self):
        try:
            most_recent_entity_version = sorted(self.entityversion_set.all(), key=lambda x: x.start_date)
            return most_recent_entity_version[-1].acronym
        except IndexError:
            return None

    @property
    def most_recent_entity_version(self):
        try:
            most_recent_entity_version = sorted(self.entityversion_set.all(), key=lambda x: x.start_date)
            return most_recent_entity_version[-1]
        except IndexError:
            return None

    class Meta:
        verbose_name_plural = "entities"

    def has_address(self):
        return self.location and self.postal_code and self.city

    # TODO :: remove this function and use annotation (most_recent_entity_version)
    def get_latest_entity_version(self):
        # Sometimes, entity-versions is prefetch to optimized queries
        if getattr(self, "entity_versions", None):
            return self.entity_versions[-1]
        return self.entityversion_set.order_by('start_date').last()


def search(**kwargs):
    queryset = Entity.objects

    if 'acronym' in kwargs:
        queryset = queryset.filter(
            entityversion__acronym__icontains=kwargs['acronym']
        )

    if 'entity_type' in kwargs:
        queryset = queryset.filter(
            entityversion__entity_type__icontains=kwargs['entity_type']
        )

    if 'version_date' in kwargs:
        queryset = queryset.filter(
            entityversion__start_date__lte=kwargs['version_date'],
            entityversion__end_date__gte=kwargs['version_date']
        )

    return queryset


def get_by_internal_id(internal_id):
    return get_object_or_none(Entity, id__exact=internal_id)


def get_by_external_id(external_id):
    return get_object_or_none(Entity, external_id__exact=external_id)


def find_versions_from_entites(entities, date):
    if date is None:
        date = timezone.now()
    order_list = [entity_type.SECTOR, entity_type.FACULTY, entity_type.SCHOOL, entity_type.INSTITUTE, entity_type.POLE]
    preserved = Case(*[When(entity_type=pk, then=pos) for pos, pk in enumerate(order_list)])
    return Entity.objects.filter(pk__in=entities). \
        filter(Q(entityversion__end_date__gte=date) | Q(entityversion__end_date__isnull=True),
               entityversion__start_date__lte=date). \
        annotate(acronym=F('entityversion__acronym')).annotate(title=F('entityversion__title')). \
        annotate(entity_type=F('entityversion__entity_type')).order_by(preserved)


def find_by_id(an_id):
    return get_object_or_none(Entity, pk=an_id)
