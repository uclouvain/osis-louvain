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
from datetime import datetime
from typing import Optional

from django.db import models
from django.db.models import F, Func, OuterRef, Subquery, Prefetch, BooleanField
from django.utils.safestring import mark_safe

from base.models.entity_version import EntityVersion
from base.models.entity_version_address import EntityVersionAddress
from base.models.enums import organization_type
from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class OrganizationAdmin(SerializableModelAdmin):
    list_display = ('name', 'acronym', 'type', 'changed', 'logo_tag')
    search_fields = ['acronym', 'name']
    list_filter = ['type']


class OrganizationManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(
            is_active=Func(
                Subquery(
                    EntityVersion.objects.filter(
                        entity__organization=OuterRef('pk'),
                    ).only_roots().order_by('-start_date').values('end_date')[:1]
                ),
                function='IS NULL',
                template='(%(expressions)s %(function)s OR %(expressions)s >= NOW())',
                output_field=BooleanField()
            ),
        )


class Organization(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, blank=True)
    acronym = models.CharField(max_length=20, blank=True)
    type = models.CharField(max_length=30, blank=True, choices=organization_type.ORGANIZATION_TYPE, default='')
    prefix = models.CharField(max_length=30, blank=True)
    logo = models.ImageField(upload_to='organization_logos', null=True, blank=True)

    objects = OrganizationManager()

    def __str__(self):
        return "{}".format(self.name)

    def logo_tag(self):
        if self.logo:
            return mark_safe('<img src="%s" height="30"/>' % self.logo.url)
        return ""

    logo_tag.short_description = 'Logo'

    class Meta:
        ordering = (F("is_active").desc(), "name")
        permissions = (
            ("can_access_organization", "Can access organization"),
        )

    @property
    def country(self):
        return getattr(self.main_address, 'country', None)

    @property
    def start_date(self):
        # Get the earliest root entity version
        root_entity_version = EntityVersion.objects.filter(entity__organization=self.pk).only_roots().order_by(
            'start_date'
        ).first()
        if root_entity_version:
            return root_entity_version.start_date
        return None

    @property
    def end_date(self):
        # Get the latest root entity version
        root_entity_version = EntityVersion.objects.filter(entity__organization=self.pk).only_roots().order_by(
            '-start_date'
        ).first()
        if root_entity_version:
            return root_entity_version.end_date
        return None

    @property
    def main_address(self) -> 'EntityVersionAddress':
        root_entity_version = self.__get_current_root_entity_version()
        if root_entity_version:
            return next(
                (address for address in root_entity_version.entityversionaddress_set.all() if address.is_main),
                None
            )
        return None

    @property
    def website(self) -> Optional[str]:
        root_entity_version = self.__get_current_root_entity_version()
        if root_entity_version:
            return root_entity_version.entity.website
        return None

    def __get_current_root_entity_version(self) -> EntityVersion:
        return EntityVersion.objects.current(datetime.now()).filter(entity__organization=self.pk).only_roots()\
            .prefetch_related(
                Prefetch(
                    'entityversionaddress_set',
                    queryset=EntityVersionAddress.objects.all().select_related('country')
                )
            ).order_by('-start_date').first()
