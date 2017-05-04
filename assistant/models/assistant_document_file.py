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


class AssistantDocumentFile(models.Model):
    document_file = models.ForeignKey('osis_common.documentFile')
    assistant_mandate = models.ForeignKey('AssistantMandate')


def search(assistant_mandate=None, description=None):
    out = None
    queryset = AssistantDocumentFile.objects.order_by('document_file__creation_date')
    if assistant_mandate:
        queryset = queryset.filter(assistant_mandate=assistant_mandate)
    if description:
        queryset = queryset.filter(document_file__description=description)
    if assistant_mandate or description:
        out = queryset
    return out


def find_first(assistant_mandate=None, description=None):
    result = search(assistant_mandate, description).first()
    if result.exists():
        return result
    return None


def find_by_document(document_file):
    return AssistantDocumentFile.objects.get(document_file=document_file)


def find_by_assistant_mandate_and_description(assistant_mandate, description):
    return AssistantDocumentFile.objects.filter(assistant_mandate=assistant_mandate).\
        filter(document_file__description=description)


def find_by_id(id_document_file):
    return AssistantDocumentFile.objects.get(id=id_document_file)


def find_by_assistant_mandate(assistant_mandate):
    return AssistantDocumentFile.objects.filter(assistant_mandate=assistant_mandate)
