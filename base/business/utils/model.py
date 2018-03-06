##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from copy import copy


def update_instance_model_from_data(instance, fields_to_update, exclude=()):
    fields_to_update_without_excluded = {field: value for field, value in fields_to_update.items()
                                         if field not in exclude}
    for field, value in fields_to_update_without_excluded.items():
        if hasattr(instance.__class__, field):
            setattr(instance, field, value)
    instance.save()


def update_related_object(obj, attribute_name, new_value):
    duplicated_obj = duplicate_object(obj)
    setattr(duplicated_obj, attribute_name, new_value)
    duplicated_obj.save()
    return duplicated_obj


def duplicate_object(obj):
    new_obj = copy(obj)
    new_obj.pk = None
    new_obj.external_id = None
    new_obj.uuid = uuid.uuid4()
    new_obj.copied_from = obj
    return new_obj
