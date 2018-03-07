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
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Case, When, Q, F
from django.utils import timezone

from base.models import entity_version
from base.models.enums import entity_type
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class EntityAdmin(SerializableModelAdmin):
    list_display = ('most_recent_acronym', 'external_id', 'organization', 'location', 'postal_code', 'phone')
    search_fields = ['external_id', 'entityversion__acronym', 'organization__acronym', 'organization__name']
    readonly_fields = ('organization', 'external_id')


class Entity(SerializableModel):
    organization = models.ForeignKey('Organization', blank=True, null=True)
    external_id = models.CharField(max_length=255, unique=True)
    changed = models.DateTimeField(null=True, auto_now=True)

    location = models.CharField(max_length=255, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    country = models.ForeignKey('reference.Country', blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    fax = models.CharField(max_length=255, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)

    @property
    def most_recent_acronym(self):
        try:
            most_recent_entity_version = self.entityversion_set.filter(entity_id=self.id).latest('start_date')
            return most_recent_entity_version.acronym
        except ObjectDoesNotExist:
            return None

    class Meta:
        verbose_name_plural = "entities"

    def has_address(self):
        return self.location and self.postal_code and self.city

    def __str__(self):
        return "{0} - {1}".format(self.most_recent_acronym, self.external_id)


def search(**kwargs):
    queryset = Entity.objects

    if 'acronym' in kwargs:
        queryset = queryset.filter(entityversion__acronym__icontains=kwargs['acronym'])

    if 'entity_type' in kwargs:
        queryset = queryset.filter(entityversion__entity_type__icontains=kwargs['entity_type'])

    if 'version_date' in kwargs:
        queryset = queryset.filter(entityversion__start_date__lte=kwargs['version_date'],
                                   entityversion__end_date__gte=kwargs['version_date'])

    return queryset


def get_by_internal_id(internal_id):
    try:
        return Entity.objects.get(id__exact=internal_id)
    except ObjectDoesNotExist:
        return None


def get_by_external_id(external_id):
    try:
        return Entity.objects.get(external_id__exact=external_id)
    except ObjectDoesNotExist:
        return None


def find_descendants(entities, date=None, with_entities=True):
    if date is None:
        date = timezone.now().date()

    entities_descendants = set()
    for entity in entities:
        entities_descendants |= _find_descendants(entity, date, with_entities)
    return list(entities_descendants)


def _find_descendants(entity, date=None, with_entities=True):
    entities_descendants = set()
    try:
        entity_vers = entity_version.get_last_version(entity, date=date)
        if with_entities:
                entities_descendants.add(entity_vers.entity)
        entities_descendants |= {entity_version_descendant.entity for entity_version_descendant in
                                 entity_vers.find_descendants(date=date)}
    finally:
        return entities_descendants


def find_versions_from_entites(entities, date):
    if date is None:
        date = timezone.now()
    order_list = [entity_type.SECTOR, entity_type.FACULTY, entity_type.SCHOOL, entity_type.INSTITUTE, entity_type.POLE]
    preserved = Case(*[When(entity_type=pk, then=pos) for pos, pk in enumerate(order_list)])
    return Entity.objects.filter(pk__in=entities).\
        filter(Q(entityversion__end_date__gte=date) | Q(entityversion__end_date__isnull=True),
               entityversion__start_date__lte=date).\
        annotate(acronym=F('entityversion__acronym')).annotate(title=F('entityversion__title')).\
        annotate(entity_type=F('entityversion__entity_type')).order_by(preserved)


def find_by_id(an_id):
    try:
        return Entity.objects.get(pk=an_id)
    except Entity.DoesNotExist:
        return None
