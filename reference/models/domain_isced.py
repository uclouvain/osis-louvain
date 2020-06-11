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
import uuid

from django.db import models
from django.utils.translation import gettext_lazy as _

from osis_common.models.osis_model_admin import OsisModelAdmin


class DomainIscedAdmin(OsisModelAdmin):
    list_display = ('code', 'title_fr', 'title_en', "uuid", 'is_ares')
    search_fields = ['code', 'title_fr', 'title_en', "uuid"]


class DomainIsced(models.Model):
    changed = models.DateTimeField(null=True, auto_now=True)

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    code = models.CharField(max_length=10, unique=True)
    title_fr = models.CharField(max_length=255, db_index=True)
    title_en = models.CharField(max_length=255, db_index=True)
    is_ares = models.BooleanField(default=True)

    def __str__(self):
        return '{} {}'.format(self.code, self.title_fr)

    class Meta:
        ordering = ('code',)
        verbose_name = _("ISCED")
