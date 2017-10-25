##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import ugettext_lazy as _

from decimal import Decimal, Context, Inexact

from base.business import learning_unit_year_with_context
from base.models import learning_unit_year
from base.models.enums import learning_component_year_type
from base.models.enums import learning_unit_year_subtypes
from base.models.enums import entity_container_year_link_type as entity_types


def update_volumes(learning_unit_year_id, updated_volumes):
    volumes_grouped_by_lunityear = get_volumes_grouped_by_lunityear(learning_unit_year_id, updated_volumes)
    errors = validate(volumes_grouped_by_lunityear)
    if not errors:
        _save(volumes_grouped_by_lunityear)
    return errors


def get_volumes_grouped_by_lunityear(learning_unit_year_id, updated_volumes):
    # Retrieve value from database
    volumes_grouped_by_lunityear = _get_volumes_from_db(learning_unit_year_id)
    for lunityear in volumes_grouped_by_lunityear:
        # Format str to Decimal
        updated_volume = updated_volumes.get(lunityear.id)
        # Replace volumes database by volumes entered by user
        lunityear.components = _set_volume_to_components(lunityear.components, updated_volume)
    return volumes_grouped_by_lunityear


def validate(volumes_grouped_by_lunityear):
    errors = []
    learning_unit_year_parent = _get_learning_unit_parent(volumes_grouped_by_lunityear)

    for lunityear in volumes_grouped_by_lunityear:
        # Validate constraint on learning unit component
        errors += _validate_components_data(lunityear)
        if learning_unit_year_parent and lunityear != learning_unit_year_parent:
            errors += _validate_parent_partim(learning_unit_year_parent, lunityear)
    return errors


def _save(volumes_grouped_by_lunityear):
    for lunityear in volumes_grouped_by_lunityear:
        for component, data in lunityear.components.items():
            component.hourly_volume_partial = data.get('VOLUME_Q1')
            component.planned_classes = data.get('PLANNED_CLASSES')
            component.save()
            _save_requirement_entities(component.entity_components_year, data)


def _save_requirement_entities(entity_components_year, data):
    for ecy in entity_components_year:
        link_type = ecy.entity_container_year.type
        ecy.hourly_volume_total = data.get('VOLUME_' + link_type)
        ecy.save()


def _get_volumes_from_db(learning_unit_year_id):
    luy = learning_unit_year.find_by_id(learning_unit_year_id)
    return learning_unit_year_with_context.get_with_context(
        learning_container_year_id=luy.learning_container_year
    )


def _get_learning_unit_parent(volumes_grouped_by_lunityear):
    return next((lunit_year for lunit_year in volumes_grouped_by_lunityear
                 if lunit_year.subtype == learning_unit_year_subtypes.FULL), None)


def _set_volume_to_components(components, updated_volume):
    if components and updated_volume:
        components_updated = {}
        for component, data in components.items():
            data_updated = updated_volume.get(component.id, {})
            data_updated = dict(data, **data_updated)
            components_updated[component] = _format_volumes(data_updated)
        return components_updated
    return components


def _format_volumes(volumes):
    volumes_formated = {}

    # Planned classes is an int
    try:
        volumes_formated['PLANNED_CLASSES'] = int(volumes.get('PLANNED_CLASSES', 0))
    except Exception:
        raise ValueError("planned_classes_must_be_integer")
    volumes_formated.update({k: _validate_decimals(volume) for k, volume in volumes.items()
                             if k not in ("PLANNED_CLASSES", "VOLUME_QUARTER")})

    return volumes_formated


def _validate_decimals(volume):
    volume_formated = _format_volume_to_decimal(volume)

    try:
        # Ensure that we cannot have more than 2 decimal
        return volume_formated.quantize(Decimal(10) ** -2, context=Context(traps=[Inexact]))
    except:
        raise ValueError("volume_have_more_than_2_decimal_places")


def _format_volume_to_decimal(volume):
    if isinstance(volume, str):
        volume = volume.strip().replace(',', '.')
        _check_volume_str_is_digit(volume)
    return Decimal(volume)


def _check_volume_str_is_digit(volume_str):
    if not volume_str.replace('.', '').isdigit():
        raise ValueError("volume_must_be_digit")


# Integrity validation for component
def _validate_components_data(l_unit_year):
    errors = []

    for component, data in l_unit_year.components.items():
        if not _is_tot_annual_equal_to_q1_q2(**data):
            errors.append("<b>{}/{}:</b> {}".format(l_unit_year.acronym, component.acronym, _('vol_tot_not_equal_to_q1_q2')))
        if not _is_tot_req_entities_equal_to_vol_req_entity(**data):
            types = [entity_types.REQUIREMENT_ENTITY, entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1, entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2]
            error_msg = ' + '.join([l_unit_year.entities.get(t).acronym for t in types if l_unit_year.entities.get(t)])
            error_msg += ' = {}'.format(_('vol_charge'))
            errors.append("<b>{}/{}:</b> {}".format(l_unit_year.acronym, component.acronym, error_msg))
        if not _is_tot_req_entities_equal_to_tot_annual_mult_cp(**data):
            errors.append("<b>{}/{}:</b> {}".format(l_unit_year.acronym, component.acronym, _('vol_tot_req_entities_not_equal_to_vol_tot_mult_cp')))
    return errors


def _is_tot_annual_equal_to_q1_q2(*args, **kwargs):
    total_annual = kwargs.get('VOLUME_TOTAL', 0)
    q1 = kwargs.get('VOLUME_Q1', 0)
    q2 = kwargs.get('VOLUME_Q2', 0)
    return total_annual == (q1 + q2)


def _is_tot_req_entities_equal_to_vol_req_entity(*args, **kwargs):
    requirement_entity = kwargs.get('VOLUME_' + entity_types.REQUIREMENT_ENTITY, 0)
    additional_requirement_entity_1 = kwargs.get('VOLUME_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1, 0)
    additional_requirement_entity_2 = kwargs.get('VOLUME_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2, 0)
    total_requirement_entities = kwargs.get('VOLUME_TOTAL_REQUIREMENT_ENTITIES', 0)

    return total_requirement_entities == (requirement_entity + additional_requirement_entity_1 +
                                          additional_requirement_entity_2)


def _is_tot_req_entities_equal_to_tot_annual_mult_cp(*args, **kwargs):
    total_annual = kwargs.get('VOLUME_TOTAL', 0)
    cp = kwargs.get('PLANNED_CLASSES', 0)
    total_requirement_entities = kwargs.get('VOLUME_TOTAL_REQUIREMENT_ENTITIES', 0)
    return total_requirement_entities == (total_annual * cp)


# Integrity validation between PARENT and PARTIM
def _validate_parent_partim(learning_unit_year_parent, learning_unit_year_partim):
    errors = []

    # Check CM
    errors += _validate_parent_partim_by_type(learning_unit_year_parent, learning_unit_year_partim,
                                              learning_component_year_type.LECTURING)
    # Check TP
    errors += _validate_parent_partim_by_type(learning_unit_year_parent, learning_unit_year_partim,
                                              learning_component_year_type.PRACTICAL_EXERCISES)
    return errors


def _validate_parent_partim_by_type(learning_unit_year_parent, learning_unit_year_partim, type):
    parent_component = next((component for component in learning_unit_year_parent.components.keys()
                             if component.type == type), None)
    partim_component = next((component for component in learning_unit_year_partim.components.keys()
                             if component.type == type), None)

    errors = _validate_parent_partim_component(learning_unit_year_parent.components[parent_component],
                                               learning_unit_year_partim.components[partim_component])

    # Prefix with acronym learning unit + acronym component
    return ["<b>{} {} / {} {}:</b> {}".format(learning_unit_year_parent.acronym, parent_component.acronym,
                                        learning_unit_year_partim.acronym, partim_component.acronym, error)
            for error in errors]


def _validate_parent_partim_component(parent_component, partim_component):
    errors = []

    partim_vol_tot = partim_component.get('VOLUME_TOTAL', 0)
    if partim_vol_tot:
        if parent_component.get('VOLUME_TOTAL', 0) <= partim_vol_tot:
            errors.append("{}".format(_('vol_tot_full_must_be_greater_than_partim')))

        if parent_component.get('VOLUME_Q1', 0) < partim_component.get('VOLUME_Q1', 0):
            errors.append("{}".format(_('vol_q1_full_must_be_greater_or_equal_to_partim')))

        if parent_component.get('VOLUME_Q2', 0) < partim_component.get('VOLUME_Q2', 0):
            errors.append("{}".format(_('vol_q2_full_must_be_greater_or_equal_to_partim')))

    partim_planned_classes = partim_component.get('PLANNED_CLASSES', 0)
    if partim_planned_classes and parent_component.get('PLANNED_CLASSES', 0) < partim_planned_classes:
        errors.append("{}".format(_('planned_classes_full_must_be_greater_or_equal_to_partim')))

    partim_volume_entity = partim_component.get('VOLUME_' + entity_types.REQUIREMENT_ENTITY, 0)
    if partim_volume_entity and parent_component.get('VOLUME_' + entity_types.REQUIREMENT_ENTITY, 0) < \
            partim_volume_entity:
        errors.append("{}".format(_('entity_requirement_full_must_be_greater_or_equal_to_partim')))

    # Verify if we have additional_requirement entity
    additional_requirement_entity_1_key = 'VOLUME_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_1
    if additional_requirement_entity_1_key in parent_component or \
        additional_requirement_entity_1_key in partim_component:

        if parent_component.get(additional_requirement_entity_1_key, 0) < partim_component.get(additional_requirement_entity_1_key, 0):
            errors.append("{}".format(_('entity_requirement_full_must_be_greater_or_equal_to_partim')))

    additional_requirement_entity_2_key = 'VOLUME_' + entity_types.ADDITIONAL_REQUIREMENT_ENTITY_2
    if additional_requirement_entity_2_key in parent_component or \
                    additional_requirement_entity_2_key in partim_component:

        if parent_component.get(additional_requirement_entity_2_key, 0) < partim_component.get(additional_requirement_entity_2_key, 0):
            errors.append("{}".format(_('entity_requirement_full_must_be_greater_or_equal_to_partim')))

    return errors
