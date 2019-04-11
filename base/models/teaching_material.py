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
from django.db import models
from django.utils.translation import ugettext_lazy as _
from ordered_model.admin import OrderedModelAdmin
from ordered_model.models import OrderedModel
from reversion.admin import VersionAdmin

from base.business.learning_units.pedagogy import update_bibliography_changed_field_in_cms
from base.models.learning_unit_year import LearningUnitYear


class TeachingMaterialAdmin(VersionAdmin, OrderedModelAdmin):
    list_display = ('title', 'mandatory', 'learning_unit_year', 'order', 'move_up_down_links')
    readonly_fields = ['order']
    search_fields = ['title', 'learning_unit_year']
    raw_id_fields = ('learning_unit_year',)


class TeachingMaterial(OrderedModel):
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    mandatory = models.BooleanField(verbose_name=_('Is this teaching material mandatory?'))
    learning_unit_year = models.ForeignKey(LearningUnitYear, on_delete=models.CASCADE)
    order_with_respect_to = 'learning_unit_year'

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = 'bibliographies'
        ordering = ('learning_unit_year', 'order')


def find_by_learning_unit_year(learning_unit_year):
    return TeachingMaterial.objects.filter(learning_unit_year=learning_unit_year)\
                                   .order_by('order')


def postpone_teaching_materials(start_luy, commit=True):
    """
    This function override all teaching materials from start_luy until latest version of this luy
    :param start_luy: The learning unit year which we want to start postponement
    :param commit:
    :return:
    """
    teaching_materials = find_by_learning_unit_year(start_luy)
    for next_luy in [luy for luy in start_luy.find_gt_learning_units_year()]:
        # Remove all previous teaching materials
        next_luy.teachingmaterial_set.all().delete()
        # Inserts all teaching materials comes from start_luy
        to_inserts = [TeachingMaterial(title=tm.title, mandatory=tm.mandatory, learning_unit_year=next_luy)
                      for tm in teaching_materials]
        bulk_save(to_inserts, commit)

        # For sync purpose, we need to trigger an update of the bibliography when we update teaching materials
        update_bibliography_changed_field_in_cms(next_luy)


def bulk_save(teaching_materials, commit=True):
    for teaching_material in teaching_materials:
        teaching_material.save(commit)
