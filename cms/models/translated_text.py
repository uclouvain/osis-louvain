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
from ckeditor.fields import RichTextField
from django.contrib import admin
from django.db import models
from django.conf import settings
from cms.enums.entity_name import ENTITY_NAME
from .text_label import TextLabel


class TranslatedTextAdmin(admin.ModelAdmin):
    list_display = ('text_label', 'entity', 'reference', 'language', 'text',)
    ordering = ('text_label',)


class TranslatedText(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    language = models.CharField(max_length=30, null=True, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)
    text_label = models.ForeignKey(TextLabel, blank=None, null=True)
    entity = models.CharField(db_index=True, max_length=25, choices=ENTITY_NAME)
    reference = models.IntegerField(db_index=True)
    text = RichTextField(null=True)

    def __str__(self):
        return self.entity


def find_by_id(id):
    return TranslatedText.objects.get(pk=id)


def search(entity, reference, text_labels_name=None, language=None):
    queryset = TranslatedText.objects.filter(entity=entity, reference=reference)

    if language:
        queryset = queryset.filter(language=language)
    if text_labels_name:
        queryset = queryset.filter(text_label__label__in=text_labels_name)

    return queryset.select_related('text_label')