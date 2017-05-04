##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.contrib import admin
from django.utils import timezone


class ApplicationNoticeAdmin(admin.ModelAdmin):
    list_display = ('subject','notice','start_publish','stop_publish')
    fieldsets = ((None, {'fields': ('subject','notice','start_publish','stop_publish')}),)


class ApplicationNotice(models.Model):
    subject = models.CharField(max_length=255)
    notice = models.TextField()
    start_publish = models.DateTimeField()
    stop_publish = models.DateTimeField()


def find_current_notice():
    samples = ApplicationNotice.objects.filter(stop_publish__gt=timezone.now(),
                                               start_publish__lt=timezone.now()).first()
    return samples






