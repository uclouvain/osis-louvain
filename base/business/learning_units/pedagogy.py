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
    postpone_teaching_materials(luy)
    return teach_material


def delete_teaching_material(teach_material):
    luy = teach_material.learning_unit_year
    result = teach_material.delete()
    postpone_teaching_materials(luy)
    return result


def postpone_teaching_materials(luy):
    from base.models import teaching_material
    teaching_material.postpone_teaching_materials(luy)
    # For sync purpose, we need to trigger an update of the bibliography when we update teaching materials
    update_bibliography_changed_field_in_cms(luy)
