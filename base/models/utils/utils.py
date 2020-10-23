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
from enum import Enum
from typing import List, Dict, Type

from osis_common.ddd import interface


class ChoiceEnum(Enum):
    @classmethod
    def all(cls):
        return list(cls)

    @classmethod
    def choices(cls):
        return tuple((x.name, x.value) for x in cls)

    @classmethod
    def get_value(cls, key):
        return getattr(cls, key, key).value if hasattr(cls, key) else key

    @classmethod
    def get_names(cls):
        return [x.name for x in cls]

    @classmethod
    def get_values(cls):
        return [x.value for x in cls]

    def __deepcopy__(self, memodict: Dict = None) -> 'ChoiceEnum':
        return self


def get_verbose_field_value(instance, key):
    if hasattr(instance, "get_" + key + "_display"):
        value = getattr(instance, "get_" + key + "_display")()
    else:
        value = getattr(instance, key, "")
    return value


def filter_with_list_or_object(fk_name, model, **kwargs):
    return model.objects.all().filter(**{
        fk_name + ('__in' if isinstance(kwargs[fk_name], list) else ''):
            kwargs[fk_name]
    })


def get_enum_from_str(value: str, enum_class: Type[ChoiceEnum]):
    """
    :param value: The string value of the enumeration key.
    :param enum_class: The class of an enumeration (inheriting from ChoiceEnum)
    :return: An instance of enum_class given in parameter. Return None if the value is not a valid enumeration choice.
    """
    if not value:
        return None
    try:
        return enum_class[value]
    except ValueError:
        raise interface.BusinessException(
            "Invalid enum choice (value={}, enumeration_class={})".format(value, enum_class)
        )
