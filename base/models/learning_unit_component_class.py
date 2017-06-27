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


class LearningUnitComponentClassAdmin(admin.ModelAdmin):
    list_display = ('learning_unit_component', 'learning_class_year')
    fieldsets = ((None, {'fields': ('learning_unit_component', 'learning_class_year')}),)
    raw_id_fields = ('learning_class_year', 'learning_unit_component')


class LearningUnitComponentClass(models.Model):
    learning_unit_component = models.ForeignKey('LearningUnitComponent')
    learning_class_year = models.ForeignKey('LearningClassYear')

    class Meta:
        permissions = (
            ("can_access_learningunitcomponentclass", "Can access learning unit component class"),
        )


def find_by_id(learning_unit_component_class_id):
    return LearningUnitComponentClass.objects.get(pk=learning_unit_component_class_id)


def find_by_learning_class_year(learning_class_year):
    return LearningUnitComponentClass.objects.filter(learning_class_year=learning_class_year)
