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

from base.models import academic_year
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.models.teaching_material import TeachingMaterial, find_by_learning_unit_year
from cms.enums import entity_name
from cms.models import translated_text
from cms.models.text_label import TextLabel
from osis_common.utils.models import get_object_or_none


def save_teaching_material(teach_material):
    teach_material.save()
    luy = teach_material.learning_unit_year
    if is_pedagogy_data_must_be_postponed(luy):
        postpone_teaching_materials(luy)
    return teach_material


def delete_teaching_material(teach_material):
    luy = teach_material.learning_unit_year
    result = teach_material.delete()
    if is_pedagogy_data_must_be_postponed(luy):
        postpone_teaching_materials(luy)
    return result


def postpone_teaching_materials(luy, commit=True):
    """
        from base.models import teaching_material
        This function override all teaching materials from start_luy until latest version of this luy
        teaching_material.postpone_teaching_materials(luy)
        :param luy: The learning unit year which we want to start postponement
        :param commit:
        :return:
        """
    teaching_materials = find_by_learning_unit_year(luy)
    for next_luy in [luy for luy in luy.find_gt_learning_units_year()]:
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


def update_bibliography_changed_field_in_cms(learning_unit_year):
    txt_label = get_object_or_none(
        TextLabel,
        label='bibliography'
    )
    if txt_label:
        for language in settings.LANGUAGES:
            translated_text.update_or_create(
                entity=entity_name.LEARNING_UNIT_YEAR,
                reference=learning_unit_year.id,
                text_label=txt_label,
                language=language[0],
                defaults={}
            )


def is_pedagogy_data_must_be_postponed(learning_unit_year):
    return learning_unit_year.academic_year.year >= academic_year.starting_academic_year().year \
           and not ProposalLearningUnit.objects.filter(
        learning_unit_year__learning_unit=learning_unit_year.learning_unit
    ).exists()
