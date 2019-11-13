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
from django.utils.translation import gettext_lazy as _

FIELDS_FOR_LEARNING_UNIT_YR_COMPARISON = ['acronym', 'internship_subtype', 'credits', 'periodicity',
                                          'status', 'language', 'professional_integration', 'specific_title',
                                          'specific_title_english', 'quadrimester',
                                          'session', 'attribution_procedure']
FIELDS_FOR_LEARNING_CONTAINER_YR_COMPARISON = ['team', 'is_vacant', 'type_declaration_vacant', 'common_title',
                                               'common_title_english']
DEFAULT_VALUE_FOR_NONE = '-'
LEARNING_COMPONENT_YEAR = 'learning_component_year'


def get_value(model, data, field_name):
    value = data.get(field_name, DEFAULT_VALUE_FOR_NONE)
    if model._meta.get_field(field_name).choices:
        return _(value) if value else DEFAULT_VALUE_FOR_NONE
    elif model._meta.get_field(field_name).get_internal_type() == 'BooleanField':
        return _decrypt_boolean_value(field_name, value)
    else:
        return value


def _get_boolean_translation(value):
    return _('yes') if value else _('no')


def _get_status(value):
    return _('Active') if value else _('Inactive')


def _decrypt_boolean_value(field_name, value):
    if field_name == 'status':
        return _get_status(value)
    else:
        return _get_boolean_translation(value)


def compare_learning_component_year(obj_ref, obj_prev, obj_next):
    data = {'ref': obj_ref, 'prev': obj_prev, 'next': obj_next}
    d = {}
    d = compare_l_component_yr_attribute(d, data, 'acronym')

    d = compare_l_component_yr_attribute(d, data, 'planned_classes')
    if _real_classes_is_different(obj_prev, obj_ref) or \
            _real_classes_is_different(obj_next, obj_ref):
        d.update({'real_classes': [obj_prev.real_classes, obj_ref.real_classes, obj_next.real_classes]})

    return d


def compare_volumes(current_data, prev_data, next_data):
    current_volumes = current_data.get('volumes') or {}
    prev_volumes = prev_data.get('volumes') or {}
    next_volumes = next_data.get('volumes') or {}

    vol = {}
    if current_volumes:
        vol = {key: [prev_volumes.get(key), value, next_volumes.get(key)]
               for key, value in current_volumes.items()
               if _is_key_to_compare(key, vol) and (value != prev_volumes.get(key) or value != next_volumes.get(key))
               }
    return vol


def get_learning_component_yr_by_type(data, learning_component_yr_type):
    for elt in data:
        if elt.get(LEARNING_COMPONENT_YEAR).type == learning_component_yr_type:
            return elt
    return {}


def component_has_changed(learning_component_yr_changes, volume_changes):
    return learning_component_yr_changes != {} or volume_changes != {}


def compare_l_component_yr_attribute(d_param, data, attribute):
    d = d_param
    obj_ref = _get_model_dict(data, 'ref')
    obj_prev = _get_model_dict(data, 'prev')
    obj_next = _get_model_dict(data, 'next')

    if _is_different(attribute, obj_prev, obj_ref) or \
            _is_different(attribute, obj_next, obj_ref):
        d.update({attribute: [obj_prev.get(attribute),
                              obj_ref.get(attribute),
                              obj_next.get(attribute)]})
    return d


def can_compare(obj_prev, obj_ref):
    return obj_ref and obj_prev


def _get_model_dict(data, key):
    obj = data.get(key)
    if obj:
        return obj.__dict__
    return {}


def _is_different(attribute, obj_prev, obj_ref):
    return can_compare(obj_ref, obj_prev) and obj_ref.get(attribute) != obj_prev.get(attribute)


def _real_classes_is_different(obj_prev, obj_ref):
    return can_compare(obj_ref, obj_prev) and obj_ref.real_classes != obj_prev.real_classes


def _is_key_to_compare(key, vol):
    return not(key == 'PLANNED_CLASSES' or key in vol)


def get_partims_as_str(partim_list):
    return ', '.join(sorted(str(partim.subdivision) for partim in partim_list))
