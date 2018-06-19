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
from django.contrib.admin import ModelAdmin
from django.db import models
from django.utils.translation import pgettext_lazy as _

from base.models.learning_unit_year import LearningUnitYear


class TeachingMaterialAdmin(ModelAdmin):
    list_display = ('title', 'mandatory', 'learning_unit_year')
    search_fields = ['title', 'learning_unit_year']
    raw_id_fields = ('learning_unit_year',)


class TeachingMaterial(models.Model):
    title = models.CharField(max_length=255, verbose_name=_('teachingmaterial', 'title'))
    mandatory = models.BooleanField(verbose_name=_('teachingmaterial', 'mandatory'))
    learning_unit_year = models.ForeignKey(LearningUnitYear, on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'bibliographies'


def find_by_learning_unit_year(learning_unit_year):
    return TeachingMaterial.objects.filter(learning_unit_year=learning_unit_year)


def build_list_of_teaching_material_content_by_learning_unit_year(learning_unit_year):
    return [
        (material.title, material.mandatory)
        for material in find_by_learning_unit_year(learning_unit_year)
    ]
