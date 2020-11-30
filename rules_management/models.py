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
from django import forms
from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.db import models

from osis_common.models.osis_model_admin import OsisModelAdmin
from rules_management import enums


class AdminForm(forms.ModelForm):
    content_type = forms.ModelChoiceField(queryset=ContentType.objects.all().order_by('model'))


class FieldReferenceAdmin(OsisModelAdmin):
    list_display = ('content_type', 'field_name', 'context')
    search_fields = ('content_type__model', 'field_name', 'context',)
    filter_horizontal = ('permissions', 'groups',)
    list_filter = ('context',)
    form = AdminForm


class FieldReferenceManager(models.Manager):
    def get_by_natural_key(self, content_type, context, field_name):
        return self.get(content_type=content_type, context=context, field_name=field_name)


class FieldReference(models.Model):
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    field_name = models.CharField(max_length=50)
    context = models.CharField(max_length=50,  choices=enums.CONTEXT_CHOICES, blank=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    groups = models.ManyToManyField(Group, blank=True)

    objects = FieldReferenceManager()

    class Meta:
        unique_together = [['content_type', 'context', 'field_name']]

    def natural_key(self):
        return (self.content_type, self.context, self.field_name)
