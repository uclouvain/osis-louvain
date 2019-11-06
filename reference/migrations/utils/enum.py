# ##################################################################################################
#  OSIS stands for Open Student Information System. It's an application                            #
#  designed to manage the core business of higher education institutions,                          #
#  such as universities, faculties, institutes and professional schools.                           #
#  The core business involves the administration of students, teachers,                            #
#  courses, programs and so on.                                                                    #
#                                                                                                  #
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)              #
#                                                                                                  #
#  This program is free software: you can redistribute it and/or modify                            #
#  it under the terms of the GNU General Public License as published by                            #
#  the Free Software Foundation, either version 3 of the License, or                               #
#  (at your option) any later version.                                                             #
#                                                                                                  #
#  This program is distributed in the hope that it will be useful,                                 #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of                                  #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                                   #
#  GNU General Public License for more details.                                                    #
#                                                                                                  #
#  A copy of this license - GNU General Public License - is available                              #
#  at the root of the source code of this program.  If not,                                        #
#  see http://www.gnu.org/licenses/.                                                               #
# ##################################################################################################
from django.conf import settings
from django.db import connection
from django.utils import translation
from django.utils.translation import gettext_lazy as _

from reference.models.enums import institutional_grade_type as instit_grade_type_enum


def get_key_from_value_institu_great_type_enum(instit_grade_type_name):
    if not instit_grade_type_name:
        return None
    for key, value in instit_grade_type_enum.INSTITUTIONAL_GRADE_CHOICES:
        lang_dict = {lang[0]: [] for lang in settings.LANGUAGES}
        for lang in lang_dict:
            translation.activate(lang)
            if _(value) == instit_grade_type_name or value == instit_grade_type_name or key == instit_grade_type_name:
                translation.deactivate()
                return key
            translation.deactivate()
    return None


def move_fk_to_enum(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute("select gt.id, igt.name from reference_gradetype gt, reference_institutionalgradetype igt where gt.institutional_grade_type_id = igt.id");
        all_gt_instit_gt = cursor.fetchall()
    for grade_type_id, instit_grade_type_name in all_gt_instit_gt:
        key = get_key_from_value_institu_great_type_enum(instit_grade_type_name)
        with connection.cursor() as cursor:
            cursor.execute("update reference_gradetype set institutional_grade_type = %s where id= %s ", [key, grade_type_id])
