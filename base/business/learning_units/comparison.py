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
from django.utils.translation import ugettext_lazy
from base.models import entity_container_year as mdl_entity_container_year
from base.models.enums import learning_component_year_type
from base.models.learning_unit_year import LearningUnitYear
from base.models.learning_component_year import LearningComponentYear
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist

FIELDS_FOR_LEARNING_UNIT_YR_COMPARISON = ['acronym', 'subtype', 'internship_subtype', 'credits', 'periodicity',
                                          'status', 'language', 'professional_integration', 'specific_title',
                                          'specific_title_english', 'quadrimester',
                                          'session', 'attribution_procedure']
FIELDS_FOR_LEARNING_CONTAINER_YR_COMPARISON = ['team', 'is_vacant', 'type_declaration_vacant']
FIELDS_FOR_LEARNING_COMPONENT_COMPARISON = ['acronym', 'real_classes', 'planned_classes']
DEFAULT_VALUE_FOR_NONE = '-'
LEARNING_COMPONENT_YEAR = 'learning_component_year'


def get_keys(list1, list2):
    keys = list1
    for k in list2:
        if k not in keys:
            keys.append(k)
    return sorted(keys, key=ugettext_lazy)


def compare_learning_unit_years(obj_ref, obj):
    data_obj1, data_obj2 = obj_ref.__dict__, obj.__dict__
    return _get_changed_values(data_obj1, data_obj2, FIELDS_FOR_LEARNING_UNIT_YR_COMPARISON, type(obj_ref))


def compare_learning_container_years(obj_ref, obj):
    data_obj1, data_obj2 = obj_ref.__dict__, obj.__dict__
    return _get_changed_values(data_obj1, data_obj2, FIELDS_FOR_LEARNING_CONTAINER_YR_COMPARISON, type(obj_ref))


def _get_changed_values(data_obj1, data_obj2, included_keys, model):
    changed_values = {}
    for key, value in data_obj1.items():
        if key not in included_keys:
            continue
        try:
            if value != data_obj2[key]:
                changed_values.update({key: get_value(model, data_obj2, key)})
        except KeyError:
            raise KeyError('Invalid key for learning_unit_year compare')
    return changed_values


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
    current_volumes = current_data.get('volumes')
    prev_volumes = prev_data.get('volumes')
    next_volumes = next_data.get('volumes')

    vol = {}
    if current_volumes:
        vol = {key: [prev_volumes.get(key), value, next_volumes.get(key)]
               for key, value in current_volumes.items()
               if _is_key_to_compare(key, vol) and (value != prev_volumes.get(key) or value != next_volumes.get(key))
               }
    return vol


def get_components_changes(previous_components, current_components, next_components):
    component_types = [learning_component_year_type.PRACTICAL_EXERCISES, learning_component_year_type.LECTURING]

    changed_values_by_component_type = []
    for a_component_type in component_types:
        current_learning_comp_yr = get_learning_component_yr_by_type(current_components, a_component_type)
        previous_learning_comp_yr = get_learning_component_yr_by_type(previous_components, a_component_type)
        next_learning_comp_yr = get_learning_component_yr_by_type(next_components, a_component_type)
        learning_component_yr_changes = compare_learning_component_year(
            current_learning_comp_yr.get(LEARNING_COMPONENT_YEAR),
            previous_learning_comp_yr.get(LEARNING_COMPONENT_YEAR),
            next_learning_comp_yr.get(LEARNING_COMPONENT_YEAR))

        volume_changes = compare_volumes(current_learning_comp_yr,
                                         previous_learning_comp_yr,
                                         next_learning_comp_yr)

        if component_has_changed(learning_component_yr_changes, volume_changes):
            learning_component_yr_changes.update({'type': _(a_component_type).lower()})
            changed_values_by_component_type.append(
                dict(list(learning_component_yr_changes.items()) + list(volume_changes.items())))
    return changed_values_by_component_type


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


def get_entity_by_type(luy, entity_type):
    try:
        entity_container_yr = mdl_entity_container_year.search(
            link_type=entity_type, learning_container_year=luy.learning_container_year
        ).get()
        return entity_container_yr.entity
    except (MultipleObjectsReturned, ObjectDoesNotExist):
        return None
