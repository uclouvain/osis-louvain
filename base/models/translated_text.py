##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
from base.enums.entity_name import ENTITY_NAME
from ckeditor.fields import RichTextField


class TranslatedTextAdmin(admin.ModelAdmin):
    list_display = ('entity_name', 'reference', 'language', 'text_label', 'text', )
    fieldsets = ((None, {'fields': ('entity_name', 'reference', 'language', 'text_label', 'text')}),)
    search_fields = ['acronym']


class TranslatedText(models.Model):
    entity_name = models.CharField(max_length=25, choices=ENTITY_NAME)
    reference = models.CharField(max_length=50, db_index=True)
    language = models.ForeignKey('reference.Language')
    text_label = models.ForeignKey('TextLabel')
    text = RichTextField()


def find_by_id(translated_text_id):
    return TranslatedText.objects.get(pk=translated_text_id)
