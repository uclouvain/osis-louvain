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
from django.contrib import admin
from django.db import models
from django.utils.translation import ugettext_lazy as _

from attribution.models.enums.function import Functions


class TutorApplicationAdmin(admin.ModelAdmin):
    list_display = ('tutor', 'function', 'learning_container_year', 'volume_lecturing', 'volume_pratical_exercice', 'changed')
    list_filter = ('learning_container_year__academic_year', )
    fieldsets = ((None, {'fields': ('last_changed', 'learning_container_year',
                                    'tutor', 'function', 'volume_lecturing', 'volume_pratical_exercice',
                                    'remark', 'course_summary')}),)
    raw_id_fields = ('learning_container_year', 'tutor')
    search_fields = ['tutor__person__first_name', 'tutor__person__last_name', 'learning_container_year__acronym',
                     'tutor__person__global_id', 'function']
    actions = ['publish_application_to_portal']

    def publish_application_to_portal(self, request, queryset):
        from attribution.business import application_json
        global_ids = list(queryset.values_list('tutor__person__global_id', flat=True))
        return application_json.publish_to_portal(global_ids)
    publish_application_to_portal.short_description = _("Publish application to portal")


class TutorApplication(models.Model):
    external_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    changed = models.DateTimeField(null=True, auto_now=True)
    learning_container_year = models.ForeignKey('base.LearningContainerYear')
    tutor = models.ForeignKey('base.Tutor')
    function = models.CharField(max_length=35, blank=True, null=True, choices=Functions.choices(), db_index=True)
    volume_lecturing = models.DecimalField(max_digits=6, decimal_places=1, blank=True, null=True)
    volume_pratical_exercice = models.DecimalField(max_digits=6, decimal_places=1, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    course_summary = models.TextField(blank=True, null=True)
    last_changed = models.DateTimeField(null=True)

    def __str__(self):
        return u"%s - %s" % (self.tutor, self.function)


def search(*args, **kwargs):
    qs = TutorApplication.objects.all()
    if "tutor" in kwargs:
        qs = qs.filter(tutor=kwargs['tutor'])
    if "learning_container_year" in kwargs:
        if isinstance(kwargs['learning_container_year'], list):
            qs = qs.filter(learning_container_year__in=kwargs['learning_container_year'])
        else:
            qs = qs.filter(learning_container_year=kwargs['learning_container_year'])
    if "global_id" in kwargs:
        if isinstance(kwargs['global_id'], list):
            qs = qs.filter(tutor__person__global_id__in=kwargs['global_id'])
        else:
            qs = qs.filter(tutor__person__global_id=kwargs['global_id'])
    return qs.select_related('tutor__person', 'learning_container_year')
