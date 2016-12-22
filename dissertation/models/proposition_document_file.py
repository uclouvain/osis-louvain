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
from osis_common.models.serializable_model import SerializableModel
from django.db import models
from django.contrib import admin


class PropositionDocumentFileAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'proposition', 'document_file')
    raw_id_fields = ('proposition', 'document_file')
    search_fields = ('uuid', 'proposition', 'document_file')


class PropositionDocumentFile(SerializableModel):
    proposition = models.ForeignKey('PropositionDissertation')
    document_file = models.ForeignKey('osis_common.documentFile')

    def __str__(self):
        return str(self.proposition)


def search(proposition=None, description=None):
    out = None
    queryset = PropositionDocumentFile.objects.order_by('document_file__creation_date')
    if proposition:
        queryset = queryset.filter(proposition=proposition)
    if description:
        queryset = queryset.filter(document_file__description=description)
    if proposition or description:
        out = queryset
    return out


def find_first(proposition=None, description=None):
    results = search(proposition, description)
    if results.exists():
        return results[0]
    return None


def find_by_document(document_file):
    return PropositionDocumentFile.objects.filter(document_file=document_file)


def find_by_proposition(proposition):
    return PropositionDocumentFile.objects.filter(proposition=proposition)
