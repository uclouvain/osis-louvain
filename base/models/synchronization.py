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
from django.utils import timezone

from osis_common.models.osis_model_admin import OsisModelAdmin


class SynchronizationAdmin(OsisModelAdmin):
    list_display = ('date',)
    search_fields = ['date']
    ordering = ('date',)


class Synchronization(models.Model):
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return "{}".format(self.date)


def find_last_synchronization_date():
    sync = Synchronization.objects.filter(date__isnull=False)
    if sync:
        return sync.order_by('-date').first().date
    else:
        return None

