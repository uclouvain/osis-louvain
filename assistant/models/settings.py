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


class SettingsAdmin(admin.ModelAdmin):
    list_display = ('starting_date', 'ending_date')


class Settings(models.Model):
    starting_date = models.DateField()
    ending_date = models.DateField()
    assistants_starting_date = models.DateField()
    assistants_ending_date = models.DateField()

    def __str__(self):
        return u"%s - %s" % (self.starting_date, self.ending_date)


def get_settings():
    return Settings.objects.first()


def access_to_procedure_is_open():
    return Settings.objects.filter(starting_date__lt=timezone.now(),
                                   ending_date__gt=timezone.now()).count() > 0


def assistants_can_see_file():
    return Settings.objects.filter(assistants_starting_date__lt=timezone.now(),
                                   assistants_ending_date__gt=timezone.now()).count() > 0
