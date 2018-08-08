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
from django.core import serializers
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from osis_common.models.serializable_model import SerializableModel, SerializableModelAdmin


class LanguageAdmin(SerializableModelAdmin):
    list_display = ('code', 'name', 'recognized')
    list_filter = ('recognized',)
    ordering = ('code',)
    search_fields = ['code', 'name']


class CountryManager(models.Manager):
    """Enable fixtures using self.code instead of `id`"""

    def get_by_natural_key(self, code):
        return self.get(code=code)


class Language(SerializableModel):
    code = models.CharField(max_length=4, unique=True)
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    name = models.CharField(max_length=80, unique=True)
    recognized = models.BooleanField(default=False)

    def __str__(self):
        return self.name


def find_by_id(language_id):
    try:
        return Language.objects.get(pk=language_id)
    except ObjectDoesNotExist:
        return None


def find_by_code(code):
    return Language.objects.get(code=code)


def serialize_list(list_languages):
    """
    Serialize a list of "Language" objects using the json format.
    Use to send data to osis-portal.
    :param list_languages: a list of "Language" objects
    :return: the serialized list (a json)
    """
    return serializers.serialize("json", list_languages)


def find_all_languages():
    languages = Language.objects.all().order_by('name')
    return languages
