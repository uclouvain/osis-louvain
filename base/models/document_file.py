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
import uuid
from django.db import models
from django.contrib import admin
from django.contrib.auth.models import User
from django.utils import timezone


class DocumentFileAdmin(admin.ModelAdmin):
    list_display = ('name', 'content_type', 'creation_date', 'size')
    fieldsets = ((None, {'fields': ('name', 'content_type', 'creation_date', 'storage_duration', 'full_path',
                                    'physical_name', 'physical_extension', 'description', 'user', 'sub_directory',
                                    'size')}),)
    readonly_fields = ('creation_date', 'physical_name')
    search_fields = ('name', 'user')


class DocumentFile(models.Model):
    CONTENT_TYPE_CHOICES = (('APPLICATION_CSV', 'application/csv'),
                            ('APPLICATION_DOC', 'application/doc'),
                            ('APPLICATION_PDF', 'application/pdf'),
                            ('APPLICATION_XLS', 'application/xls'),
                            ('APPLICATION_XLSX', 'application/xlsx'),
                            ('APPLICATION_XML', 'application/xml'),
                            ('APPLICATION_ZIP', 'application/zip'),
                            ('IMAGE_JPEG', 'image/jpeg'),
                            ('IMAGE_GIF', 'image/gif'),
                            ('IMAGE_PNG', 'image/png'),
                            ('TEXT_HTML', 'text/html'),
                            ('TEXT_PLAIN', 'text/plain'),)

    name = models.CharField(max_length=100)
    content_type = models.CharField(max_length=50, choices=CONTENT_TYPE_CHOICES)
    creation_date = models.DateTimeField(auto_now=True, editable=False)
    storage_duration = models.IntegerField()
    full_path = models.CharField(max_length=255)
    physical_name = models.UUIDField(default=uuid.uuid4, editable=False)
    physical_extension = models.CharField(max_length=10)
    description = models.CharField(max_length=255, null=True, blank=True)
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    sub_directory = models.CharField(max_length=100, null=True, blank=True)
    size = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name


def find_by_id(document_file_id):
    return DocumentFile.objects.get(pk=document_file_id)

def search(username=None, creation_date=None):
    queryset = DocumentFile.objects

    if username:
        queryset = queryset.filter(user__username__icontains=username)

    if creation_date:
        queryset = queryset.filter(creation_date__year=creation_date.year,creation_date__month=creation_date.month,creation_date__day=creation_date.day)

    return queryset
