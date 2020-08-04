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
from django.contrib.gis.db.models import PointField
from django.db import models
from reversion.admin import VersionAdmin

from osis_common.models.osis_model_admin import OsisModelAdmin


class EntityVersionAddressAdmin(VersionAdmin, OsisModelAdmin):
    list_display = ('id', 'entity_version_id', 'is_main', 'country', 'state', 'city', 'postal_code',)
    search_fields = ['city', 'street', 'postal_code', 'country__name', 'state', 'entity_version__id']
    raw_id_fields = ('country', 'entity_version')
    list_filter = ['is_main', 'country']

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('country')


class EntityVersionAddress(models.Model):
    changed = models.DateTimeField(null=True, auto_now=True)
    city = models.CharField(max_length=255, blank=True)
    street = models.CharField(max_length=255, blank=True)
    street_number = models.CharField(max_length=12, blank=True)
    postal_code = models.CharField(max_length=32, blank=True)
    state = models.CharField(max_length=255, blank=True)
    country = models.ForeignKey('reference.Country', on_delete=models.PROTECT, blank=True, null=True)
    entity_version = models.ForeignKey('EntityVersion', on_delete=models.PROTECT)
    location = PointField(blank=True, null=True)
    is_main = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['entity_version'],
                condition=models.Q(is_main=True),
                name='unique_main_address',
            )
        ]
