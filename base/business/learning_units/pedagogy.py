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
from cms.enums import entity_name
from cms.models import text_label, translated_text


def update_bibliography_changed_field_in_cms(learning_unit_year):
    txt_label = text_label.get_by_label_or_none('bibliography')
    if txt_label:
        for language in settings.LANGUAGES:
            translated_text.update_or_create(
                entity=entity_name.LEARNING_UNIT_YEAR,
                reference=learning_unit_year.id,
                text_label=txt_label,
                language=language[0],
                defaults={}
            )


def save_teaching_material(teach_material):
    teach_material.save()
    luy = teach_material.learning_unit_year
    check_teaching_materials_postponement(luy)
    return teach_material


def delete_teaching_material(teach_material):
    luy = teach_material.learning_unit_year
    result = teach_material.delete()
    check_teaching_materials_postponement(luy)
    return result


def check_teaching_materials_postponement(luy):
    if can_teaching_material_data_be_postponed(luy):
        from base.models import teaching_material
        teaching_material.postpone_teaching_materials(luy)
    # For sync purpose, we need to trigger an update of the bibliography when we update teaching materials
    update_bibliography_changed_field_in_cms(luy)


def can_teaching_material_data_be_postponed(learning_unit_year):
    # We must postpone pedagogy information, if we modify data form N+1
    current_academic_year = academic_year.starting_academic_year()
    return learning_unit_year.academic_year.year > current_academic_year.year
