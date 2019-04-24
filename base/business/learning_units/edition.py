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
from django.db import IntegrityError, transaction, Error
from django.db.models import F
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from base import models as mdl_base
from base.business import learning_unit_year_with_context
from base.business.learning_units.simple.deletion import delete_from_given_learning_unit_year, \
    check_learning_unit_year_deletion
from base.business.utils.model import update_instance_model_from_data, update_related_object
from base.models import entity_component_year
from base.models import entity_container_year, learning_component_year, learning_class_year
from base.models.academic_year import AcademicYear, compute_max_academic_year_adjournment
from base.models.entity_component_year import EntityComponentYear
from base.models.entity_container_year import EntityContainerYear
from base.models.entity_version import EntityVersion
from base.models.enums import learning_unit_year_periodicity, learning_unit_year_subtypes
from base.models.enums.entity_container_year_link_type import ENTITY_TYPE_LIST, REQUIREMENT_ENTITIES
from base.models.learning_container_year import LearningContainerYear
from base.models.learning_unit_year import LearningUnitYear
from base.models.proposal_learning_unit import is_learning_unit_year_in_proposal
from cms.models import translated_text

FIELDS_TO_EXCLUDE_WITH_REPORT = ("is_vacant", "type_declaration_vacant", "attribution_procedure")


# TODO :: Use LearningUnitPostponementForm to extend/shorten a LearningUnit and remove all this code
def edit_learning_unit_end_date(learning_unit_to_edit, new_academic_year, propagate_end_date_to_luy=True):
    result = []
    new_end_year = _get_new_end_year(new_academic_year)

    if propagate_end_date_to_luy:
        result.extend(_update_learning_unit_year_end_date(learning_unit_to_edit, new_academic_year, new_end_year))

    result.append(_update_end_year_field(learning_unit_to_edit, new_end_year))
    return result


def _update_learning_unit_year_end_date(learning_unit_to_edit, new_academic_year, new_end_year):
    end_year = _get_actual_end_year(learning_unit_to_edit)
    if new_end_year is None or new_end_year > end_year:
        return extend_learning_unit(learning_unit_to_edit, new_academic_year)
    elif new_end_year < end_year:
        return shorten_learning_unit(learning_unit_to_edit, new_academic_year)
    return []


# TODO :: Use LearningUnitPostponementForm to extend/shorten a LearningUnit and remove all this code
def shorten_learning_unit(learning_unit_to_edit, new_academic_year):
    _check_shorten_partims(learning_unit_to_edit, new_academic_year)

    learning_unit_year_to_delete = LearningUnitYear.objects.filter(
        learning_unit=learning_unit_to_edit,
        academic_year__year__gte=new_academic_year.year + 1
    ).order_by('academic_year').first()

    if not learning_unit_year_to_delete:
        return []

    warning_msg = check_learning_unit_year_deletion(learning_unit_year_to_delete)
    if warning_msg:
        raise IntegrityError(list(warning_msg.values()))

    with transaction.atomic():
        result = delete_from_given_learning_unit_year(learning_unit_year_to_delete)
    return result


# TODO :: Use LearningUnitPostponementForm to extend/shorten a LearningUnit and remove all this code
def extend_learning_unit(learning_unit_to_edit, new_academic_year):
    result = []
    last_learning_unit_year = LearningUnitYear.objects.filter(
        learning_unit=learning_unit_to_edit
    ).order_by('academic_year').last()

    _check_extend_partim(last_learning_unit_year, new_academic_year)

    if not new_academic_year:  # If there is no selected academic_year, we take the maximal value
        new_academic_year = AcademicYear.objects.max_adjournment()

    with transaction.atomic():
        for ac_year in get_next_academic_years(learning_unit_to_edit, new_academic_year.year):
            new_luy = duplicate_learning_unit_year(last_learning_unit_year, ac_year)
            result.append(create_learning_unit_year_creation_message(new_luy))

    return result


def _check_extend_partim(last_learning_unit_year, new_academic_year):
    if not new_academic_year:  # If there is no selected academic_year, we take the maximal value
        new_academic_year = AcademicYear.objects.max_adjournment(delta=1)

    lu_parent = last_learning_unit_year.parent
    if last_learning_unit_year.is_partim() and lu_parent:
        if _get_actual_end_year(lu_parent.learning_unit) < new_academic_year.year:
            raise IntegrityError(
                _('The selected end year (%(partim_end_year)s) is greater '
                  'than the end year of the parent %(lu_parent)s') % {
                    'partim_end_year': new_academic_year,
                    'lu_parent': lu_parent.acronym
                }
            )


def _update_end_year_field(lu, year):
    lu.end_year = year
    lu.save()
    return _('Learning unit %(acronym)s successfully updated.') % {
        'acronym': lu.acronym,
    }


def duplicate_learning_unit_year(old_learn_unit_year, new_academic_year):
    duplicated_luy = update_related_object(old_learn_unit_year, 'academic_year', new_academic_year)
    duplicated_luy.attribution_procedure = None
    duplicated_luy.learning_container_year = _duplicate_learning_container_year(
        duplicated_luy,
        new_academic_year,
        old_learn_unit_year
    )
    _duplicate_teaching_material(duplicated_luy)
    _duplicate_cms_data(duplicated_luy)
    duplicated_luy.save()

    _duplicate_external(old_learn_unit_year, duplicated_luy)

    return duplicated_luy


def _duplicate_external(old_learning_unit_year, new_learning_unit_year):
    if old_learning_unit_year.is_external():
        try:
            return update_related_object(
                old_learning_unit_year.externallearningunityear,
                "learning_unit_year",
                new_learning_unit_year,
            )
        # Dirty data
        except LearningUnitYear.DoesNotExist:
            pass  # TODO Maybe we should return a error


def _duplicate_learning_container_year(new_learn_unit_year, new_academic_year, old_learn_unit_year):
    duplicated_lcy = _get_or_create_container_year(new_learn_unit_year, new_academic_year)
    _duplicate_learning_component_year(duplicated_lcy, new_learn_unit_year, old_learn_unit_year)
    duplicated_lcy.save()
    return duplicated_lcy


def _get_or_create_container_year(new_learn_unit_year, new_academic_year):
    queryset = LearningContainerYear.objects.filter(
        academic_year=new_academic_year,
        learning_container=new_learn_unit_year.learning_container_year.learning_container
    )
    # Sometimes, the container already exists, we can directly use it and its entitycontaineryear
    if not queryset.exists():
        duplicated_lcy = update_related_object(new_learn_unit_year.learning_container_year,
                                               'academic_year', new_academic_year)
        duplicated_lcy.is_vacant = False
        duplicated_lcy.type_declaration_vacant = None

        _duplicate_entity_container_year(duplicated_lcy, new_academic_year)
    else:
        duplicated_lcy = queryset.get()
        duplicated_lcy.copied_from = new_learn_unit_year.learning_container_year
    return duplicated_lcy


def _duplicate_entity_container_year(new_lcy, new_academic_year):
    for entity_container_y in entity_container_year.search(learning_container_year=new_lcy.copied_from):
        entity_versions = EntityVersion.objects.entity(entity_container_y.entity)
        if not entity_versions.current(new_academic_year.end_date).exists():
            raise IntegrityError(
                _('The entity %(entity_acronym)s does not exist for the selected academic year %(academic_year)s') % {
                    'entity_acronym': entity_versions.last().acronym,
                    'academic_year': new_academic_year
                })
        update_related_object(entity_container_y, 'learning_container_year', new_lcy)


def _duplicate_learning_component_year(new_learn_container_year, new_learn_unit_year, old_learn_unit_year):
    old_components = old_learn_unit_year.learningcomponentyear_set.all()
    for old_component in old_components:
        new_component = update_related_object(old_component, 'learning_unit_year', new_learn_unit_year)
        _duplicate_learning_class_year(new_component)
        _duplicate_entity_component_year(new_component, new_learn_container_year)


def _duplicate_entity_component_year(new_component, new_learn_container_year):
    for old_entity_comp_year in EntityComponentYear.objects.filter(learning_component_year=new_component.copied_from):
        old_entity_container = old_entity_comp_year.entity_container_year
        new_entity_container_year = EntityContainerYear.objects.get(
            learning_container_year=new_learn_container_year,
            entity=old_entity_container.entity,
            type=old_entity_container.type
        )

        new_entity_component_year = update_related_object(old_entity_comp_year,
                                                          'entity_container_year',
                                                          new_entity_container_year)
        new_entity_component_year.learning_component_year = new_component
        new_entity_component_year.save()


def _duplicate_learning_class_year(new_component):
    for old_learning_class in learning_class_year.find_by_learning_component_year(new_component.copied_from):
        update_related_object(old_learning_class, 'learning_component_year', new_component)


def _duplicate_teaching_material(duplicated_luy):
    previous_teaching_material = mdl_base.teaching_material.find_by_learning_unit_year(duplicated_luy.copied_from)
    for material in previous_teaching_material:
        update_related_object(material, 'learning_unit_year', duplicated_luy)


def _duplicate_cms_data(duplicated_luy):
    previous_cms_data = translated_text.find_by_reference(duplicated_luy.copied_from.id)
    for item in previous_cms_data:
        update_related_object(item, 'reference', duplicated_luy.id)


def _check_shorten_partims(learning_unit_to_edit, new_academic_year):
    if not LearningUnitYear.objects.filter(
            learning_unit=learning_unit_to_edit, subtype=learning_unit_year_subtypes.FULL).exists():
        return None

    for lcy in LearningContainerYear.objects.filter(learning_container=learning_unit_to_edit.learning_container):
        for partim in lcy.get_partims_related():
            _check_shorten_partim(learning_unit_to_edit, new_academic_year, partim)


def _check_shorten_partim(learning_unit_to_edit, new_academic_year, partim):
    if _get_actual_end_year(partim.learning_unit) > new_academic_year.year:
        raise IntegrityError(
            _('The learning unit %(learning_unit)s has a partim %(partim)s with '
              'an end year greater than %(year)s') % {
                'learning_unit': learning_unit_to_edit.acronym,
                'partim': partim.acronym,
                'year': new_academic_year
            }
        )


def _get_actual_end_year(learning_unit_to_edit):
    return learning_unit_to_edit.end_year or compute_max_academic_year_adjournment() + 1


def _get_new_end_year(new_academic_year):
    return new_academic_year.year if new_academic_year else None


def get_next_academic_years(learning_unit_to_edit, year):
    range_years = list(range(learning_unit_to_edit.end_year + 1, year + 1))
    return AcademicYear.objects.filter(year__in=range_years).order_by('year')


def filter_biennial(queryset, periodicity):
    result = queryset
    if periodicity != learning_unit_year_periodicity.ANNUAL:
        is_odd = periodicity == learning_unit_year_periodicity.BIENNIAL_ODD
        result = queryset.annotate(odd=F('year') % 2).filter(odd=is_odd)
    return result


# TODO :: Use LearningUnitPostponementForm to extend/shorten a LearningUnit and remove all this code
def update_learning_unit_year_with_report(luy_to_update, fields_to_update, entities_by_type_to_update, **kwargs):
    with_report = kwargs.get('with_report', True)
    override_postponement_consistency = kwargs.get('override_postponement_consistency', False)

    conflict_report = {}
    if with_report:
        conflict_report = get_postponement_conflict_report(
            luy_to_update,
            override_postponement_consistency=override_postponement_consistency
        )
        luy_to_update_list = conflict_report['luy_without_conflict']
    else:
        luy_to_update_list = [luy_to_update]

    # Update luy which doesn't have conflict
    for luy in luy_to_update_list:
        _update_learning_unit_year(luy, fields_to_update, with_report=(luy != luy_to_update))
        _update_learning_unit_year_entities(luy, entities_by_type_to_update)

    # Show conflict error if exists
    check_postponement_conflict_report_errors(conflict_report)


# TODO :: Use LearningUnitPostponementForm to extend/shorten a LearningUnit and remove all this code
def get_postponement_conflict_report(luy_start, override_postponement_consistency=False):
    """
    This function will return a list of learning unit year (luy_without_conflict) ( > luy_start)
    which doesn't have any conflict. If any conflict found, the variable 'errors' will store it.
    """
    result = {'luy_without_conflict': [luy_start]}
    for luy in luy_start.find_gt_learning_units_year():
        error_list = _check_postponement_conflict(luy_start, luy)
        if error_list and not override_postponement_consistency:
            result['errors'] = error_list
            break
        result['luy_without_conflict'].append(luy)
    return result


# TODO :: Use LearningUnitPostponementForm to extend/shorten a LearningUnit and remove all this code
def check_postponement_conflict_report_errors(conflict_report):
    if conflict_report.get('errors'):
        last_instance_updated = conflict_report.get('luy_without_conflict', [])[-1]
        raise ConsistencyError(
            last_instance_updated,
            conflict_report.get('errors'),
            _('An error occured when updating the learning unit.')
        )


# FIXME should used include and not exclude
def _update_learning_unit_year(luy_to_update, fields_to_update, with_report):
    fields_to_exclude = ()
    if with_report:
        fields_to_exclude = FIELDS_TO_EXCLUDE_WITH_REPORT

    update_instance_model_from_data(luy_to_update.learning_unit, fields_to_update, exclude=('acronym',))

    # Only the subtype FULL can edit the container
    if luy_to_update.subtype == learning_unit_year_subtypes.FULL:
        update_instance_model_from_data(luy_to_update.learning_container_year, fields_to_update,
                                        exclude=fields_to_exclude)

    update_instance_model_from_data(luy_to_update, fields_to_update,
                                    exclude=fields_to_exclude + ("in_charge",))


def _update_learning_unit_year_entities(luy, entities_by_type_to_update):
    for entity_link_type, entity, in entities_by_type_to_update.items():
        if entity:
            entity_container_yr = _update_entity_container_year(entity, luy.learning_container_year, entity_link_type)
            _create_entity_component_year_if_not_exists(entity_container_yr)
        else:
            _delete_entity_component_year(luy.learning_container_year, entity_link_type)
            _delete_entity_container_year(luy.learning_container_year, entity_link_type)


def update_or_create_entity_container_year_with_components(an_entity, learning_container_year, type_entity):
    an_entity_container_year = _update_entity_container_year(an_entity, learning_container_year, type_entity)
    if type_entity in REQUIREMENT_ENTITIES:
        # Only entity with volume can have entity_component_year
        _create_entity_component_year_if_not_exists(an_entity_container_year)


def _update_entity_container_year(an_entity, learning_container_year, type_entity):
    entity_container_yr, created = entity_container_year.EntityContainerYear.objects.update_or_create(
        type=type_entity, learning_container_year=learning_container_year, defaults={"entity": an_entity})
    return entity_container_yr


def _create_entity_component_year_if_not_exists(an_entity_container):
    """We must create an entity component year for each component (Full+Partim)"""
    learning_component_yr_list = learning_component_year.find_by_learning_container_year(
        learning_container_year=an_entity_container.learning_container_year
    )
    for learning_component_yr in learning_component_yr_list:
        entity_component_year.EntityComponentYear.objects.get_or_create(
            entity_container_year=an_entity_container,
            learning_component_year=learning_component_yr
        )


def _delete_entity_container_year(learning_container_year, type_entity):
    entity_container_year.EntityContainerYear.objects.filter(
        type=type_entity, learning_container_year=learning_container_year).delete()


def _delete_entity_component_year(learning_container_year, type_entity):
    entity_component_year.EntityComponentYear.objects.filter(
        entity_container_year__learning_container_year=learning_container_year,
        entity_container_year__type=type_entity
    ).delete()


def _check_postponement_conflict(luy, next_luy):
    error_list = []
    lcy = luy.learning_container_year
    next_lcy = next_luy.learning_container_year
    error_list.extend(_check_postponement_conflict_on_learning_unit_year(luy, next_luy))
    error_list.extend(_check_postponement_conflict_on_learning_container_year(lcy, next_lcy))
    error_list.extend(_check_postponement_conflict_on_entity_container_year(lcy, next_lcy))
    error_list.extend(_check_postponement_learning_unit_year_proposal_state(next_luy))
    error_list.extend(_check_postponement_conflict_on_volumes(lcy, next_lcy))
    return error_list


def _check_postponement_conflict_on_learning_unit_year(luy, next_luy):
    fields_to_compare = {
        'acronym': _('Acronym'),
        'specific_title': _('English title proper'),
        'specific_title_english': _('English title proper'),
        'subtype': _('Subtype'),
        'credits': _('credits'),
        'internship_subtype': _('Internship subtype'),
        'status': _('Status'),
        'session': _('Session derogation'),
        'quadrimester': _('Quadrimester'),
        'campus': _('Campus'),
        'language': _('Language'),
    }
    return _get_differences(luy, next_luy, fields_to_compare)


def _check_postponement_conflict_on_learning_container_year(lcy, next_lcy):
    fields_to_compare = {
        'container_type': _('type'),
        'common_title': _('Common title'),
        'common_title_english': _('Common English title'),
        'acronym': _('Acronym'),
        'team': _('Team management')
    }
    return _get_differences(lcy, next_lcy, fields_to_compare)


def _get_differences(obj1, obj2, fields_to_compare):
    field_diff = filter(lambda field: _is_different_value(obj1, obj2, field), fields_to_compare.keys())
    error_list = []
    for field_name in field_diff:
        current_value = getattr(obj1, field_name, None)
        next_year_value = getattr(obj2, field_name, None)
        error_list.append(_("The value of field '%(field)s' is different between year %(year)s - %(value)s "
                            "and year %(next_year)s - %(next_value)s") % {
                              'field': fields_to_compare[field_name],
                              'year': obj1.academic_year,
                              'value': _get_translated_value(current_value),
                              'next_year': obj2.academic_year,
                              'next_value': _get_translated_value(next_year_value)
                          })
    return error_list


def _get_translated_value(value):
    if value is None:
        return _('No data')
    if isinstance(value, bool):
        return _('yes') if value else _('no')
    return value


def _check_postponement_learning_unit_year_proposal_state(nex_luy):
    error_msg = _("The learning unit %(luy)s is in proposal,"
                  " can not save the change from the year %(academic_year)s") % {
                    'luy': nex_luy.acronym,
                    'academic_year': nex_luy.academic_year
                }
    return [error_msg] if is_learning_unit_year_in_proposal(nex_luy) else []


def _check_postponement_conflict_on_entity_container_year(lcy, next_lcy):
    current_entities = entity_container_year.find_entities_grouped_by_linktype(lcy)
    next_year_entities = entity_container_year.find_entities_grouped_by_linktype(next_lcy)
    error_list = _check_if_all_entities_exist(next_lcy, list(next_year_entities.values()))
    entity_type_diff = filter(lambda type: _is_different_value(current_entities, next_year_entities, type),
                              ENTITY_TYPE_LIST)
    for entity_type in entity_type_diff:
        current_entity = current_entities.get(entity_type)
        next_year_entity = next_year_entities.get(entity_type)
        error_list.append(_("The value of field '%(field)s' is different between year %(year)s - %(value)s "
                            "and year %(next_year)s - %(next_value)s") % {
                              'field': _(entity_type.lower()),
                              'year': lcy.academic_year,
                              'value': current_entity.most_recent_acronym if current_entity else _('No data'),
                              'next_year': next_lcy.academic_year,
                              'next_value': next_year_entity.most_recent_acronym if next_year_entity else _('No data')
                          })
    return error_list


def _check_if_all_entities_exist(lcy, entities_list):
    error_list = []
    date = lcy.academic_year.start_date
    entities_ids = [entity.id for entity in entities_list]
    existing_entities = mdl_base.entity.find_versions_from_entites(entities_ids, date).values_list('id', flat=True)
    entities_not_found = filter(lambda entity: entity.id not in existing_entities, entities_list)

    for entity_not_found in set(entities_not_found):
        error = _("The entity '%(acronym)s' doesn't exist anymore in %(year)s" % {
            'acronym': entity_not_found.most_recent_acronym,
            'year': lcy.academic_year
        })
        error_list.append(error)
    return error_list


def _is_different_value(obj1, obj2, field, empty_str_as_none=True):
    value_obj1 = _get_value_from_field(obj1, field)
    value_obj2 = _get_value_from_field(obj2, field)
    if empty_str_as_none:
        value_obj1 = value_obj1 or ''
        value_obj2 = value_obj2 or ''
    return value_obj1 != value_obj2


def _get_value_from_field(obj, field):
    return obj.get(field) if isinstance(obj, dict) else getattr(obj, field, None)


def _check_postponement_conflict_on_volumes(lcy, next_lcy):
    current_learning_units = learning_unit_year_with_context.get_with_context(learning_container_year_id=lcy.id)
    next_year_learning_units = learning_unit_year_with_context.get_with_context(learning_container_year_id=next_lcy.id)

    error_list = []
    for luy_with_components in current_learning_units:
        try:
            next_luy_with_components = _get_next_luy_with_components(luy_with_components, next_year_learning_units)
            error_list.extend(_check_postponement_conflict_on_components(
                luy_with_components,
                next_luy_with_components)
            )
        except StopIteration:
            error_list.append(_("There is not the learning unit %(acronym)s - %(next_year)s") % {
                'acronym': luy_with_components.acronym,
                'next_year': next_lcy.academic_year
            })
    return error_list


def _get_next_luy_with_components(luy_with_components, next_year_learning_units):
    return next(luy for luy in next_year_learning_units if
                luy.learning_unit == luy_with_components.learning_unit)


def _check_postponement_conflict_on_components(luy_with_components, next_luy_with_components):
    error_list = []

    current_components = getattr(luy_with_components, 'components', {})
    next_year_components = getattr(next_luy_with_components, 'components', {})
    for component, volumes_computed in current_components.items():
        try:
            # Get the same component for next year (Key: component type)
            next_year_component = _get_next_year_component(next_year_components, component.type)
            error_list.extend(_check_postponement_conflict_on_volumes_data(
                component, next_year_component,
                volumes_computed, next_year_components[next_year_component]
            ))
            # Pop the values when validation done
            next_year_components.pop(next_year_component)
        except StopIteration:
            # Case current year have component which doesn't exist on next year
            error = _get_error_component_not_found(luy_with_components.acronym, component.type,
                                                   luy_with_components.academic_year,
                                                   next_luy_with_components.academic_year)
            error_list.append(error)

    if next_year_components:
        # Case next year have component which doesn't exist on current year
        for component in next_year_components.keys():
            error_list.append(_get_error_component_not_found(luy_with_components.acronym, component.type,
                                                             next_luy_with_components.academic_year,
                                                             luy_with_components.academic_year))
    return error_list


def _get_next_year_component(next_year_components, component_type):
    return next(next_year_component for next_year_component in next_year_components
                if next_year_component.type == component_type)


def _check_postponement_conflict_on_volumes_data(current_component, next_year_component,
                                                 current_volumes_data, next_year_volumes_data):
    error_list = []
    volumes_fields_diff = _get_volumes_diff(current_volumes_data, next_year_volumes_data)
    for field in volumes_fields_diff:
        values_diff = {'current': current_volumes_data.get(field), 'next_year': next_year_volumes_data.get(field)}
        error_list.append(_get_error_volume_field_diff(field, current_component, next_year_component, values_diff))
    return error_list


def _get_volumes_diff(current_volumes_data, next_year_volumes_data):
    return filter(lambda data: _is_different_value(current_volumes_data, next_year_volumes_data, data),
                  current_volumes_data)


def _get_error_volume_field_diff(field_diff, current_component, next_year_component, values_diff):
    return _("The value of field '%(field)s' for the learning unit %(acronym)s (%(component_type)s) "
             "is different between year %(year)s - %(value)s and year %(next_year)s - %(next_value)s") % \
           {
               'field': _(field_diff.lower()),
               'acronym': current_component.learning_unit_year.acronym,
               'component_type': _(current_component.type) if current_component.type else 'NT',
               'year': current_component.learning_unit_year.academic_year,
               'value': values_diff.get('current') or _('No data'),
               'next_year': next_year_component.learning_unit_year.academic_year,
               'next_value': values_diff.get('next_year') or _('No data')
           }


def _get_error_component_not_found(acronym, component_type, existing_academic_year, not_found_academic_year):
    return _("There is not %(component_type)s for the learning unit %(acronym)s - %(year)s but exist in"
             " %(existing_year)s") % {
               'component_type': _(component_type),
               'acronym': acronym,
               'year': not_found_academic_year,
               'existing_year': existing_academic_year
           }


class ConsistencyError(Error):
    def __init__(self, last_instance_updated, error_list, *args, **kwargs):
        self.last_instance_updated = last_instance_updated
        self.error_list = error_list
        super().__init__(*args, **kwargs)


def create_learning_unit_year_creation_message(learning_unit_year_created):
    link = reverse("learning_unit", kwargs={'learning_unit_year_id': learning_unit_year_created.id})
    return _("Learning Unit <a href='%(link)s'> %(acronym)s (%(academic_year)s) </a> "
             "successfuly created.") % {'link': link, 'acronym': learning_unit_year_created.acronym,
                                        'academic_year': learning_unit_year_created.academic_year}
