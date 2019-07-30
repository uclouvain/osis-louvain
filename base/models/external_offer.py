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
from reversion.admin import VersionAdmin

from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class ExternalOfferAdmin(VersionAdmin, SerializableModelAdmin):
    list_display = ('name', 'adhoc', 'domain', 'grade_type', 'offer_year', 'changed')
    ordering = ('name',)
    search_fields = ['name']


class ExternalOffer(SerializableModel):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    name = models.CharField(max_length=150, unique=True)
    adhoc = models.BooleanField(default=True)  # If False == Official/validated, if True == Not Official/not validated
    domain = models.ForeignKey('reference.Domain', on_delete=models.PROTECT)
    grade_type = models.ForeignKey('reference.GradeType', blank=True, null=True, on_delete=models.PROTECT)

    # Institution equivalence ("intern" offer)
    offer_year = models.ForeignKey('base.OfferYear', blank=True, null=True, on_delete=models.PROTECT)
    national = models.BooleanField(default=False)  # True if is Belgian else False

    def __str__(self):
        return self.name
