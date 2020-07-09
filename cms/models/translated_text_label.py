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
from django.conf import settings
from django.db import models

from osis_common.models import osis_model_admin
from .text_label import TextLabel


class TranslatedTextLabelAdmin(osis_model_admin.OsisModelAdmin):
    actions = None  # Remove ability to delete in Admin Interface
    list_display = ('label', 'language', 'text_label',)
    search_fields = ['label', 'text_label__label']
    ordering = ('label',)
    list_filter = ('language',)

    def has_delete_permission(self, request, obj=None):
        return False


class TranslatedTextLabel(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    language = models.CharField(max_length=30, null=True, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE)
    text_label = models.ForeignKey(TextLabel, on_delete=models.CASCADE)
    label = models.CharField(max_length=255)

    class Meta:
        unique_together = ('language', 'text_label')

    def __str__(self):
        return self.label


def search(text_entity, labels=None, language=None):
    queryset = TranslatedTextLabel.objects.filter(text_label__entity=text_entity)
    if labels:
        queryset = queryset.filter(text_label__label__in=labels)
    if language:
        queryset = queryset.filter(language=language)

    return queryset.select_related('text_label')


def get_label_translation(text_entity: str, label: str, language: str):
    translated_text_label = search(
        text_entity=text_entity,
        labels=[label],
        language=language
    )
    return translated_text_label.get().label if translated_text_label else label
