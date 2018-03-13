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

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils.translation import ugettext_lazy as _

from base.business.learning_unit import compute_max_academic_year_adjournment
from base.business.learning_unit_deletion import delete_from_given_learning_unit_year, \
    check_learning_unit_year_deletion
from base.business.learning_unit_year_with_context import ENTITY_TYPES_VOLUME
from base.business.utils.model import update_instance_model_from_data, update_related_object
from base.models import entity_component_year
from base.models import entity_container_year, learning_component_year, learning_class_year, learning_unit_component
from base.models.academic_year import AcademicYear
from base.models.entity_component_year import EntityComponentYear
from base.models.entity_container_year import EntityContainerYear
from base.models.entity_version import EntityVersion
from base.models.enums import learning_unit_periodicity, learning_unit_year_subtypes
from base.models.learning_container_year import LearningContainerYear
from base.models.learning_unit_year import LearningUnitYear


def edit_learning_unit_end_date(learning_unit_to_edit, new_academic_year):
    result = []

    new_end_year = _get_new_end_year(new_academic_year)
    end_year = _get_actual_end_year(learning_unit_to_edit)

    if new_end_year is None or new_end_year > end_year:
        result.extend(extend_learning_unit(learning_unit_to_edit, new_academic_year))
    elif new_end_year < end_year:
        result.extend(shorten_learning_unit(learning_unit_to_edit, new_academic_year))

    result.append(_update_end_year_field(learning_unit_to_edit, new_end_year))
    return result


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


def extend_learning_unit(learning_unit_to_edit, new_academic_year):
    result = []
    last_learning_unit_year = LearningUnitYear.objects.filter(learning_unit=learning_unit_to_edit
                                                              ).order_by('academic_year').last()

    _check_extend_partim(last_learning_unit_year, new_academic_year)

    if not new_academic_year:  # If there is no selected academic_year, we take the maximal value
        new_academic_year = AcademicYear.objects.get(year=compute_max_academic_year_adjournment())

    with transaction.atomic():
        for ac_year in _get_next_academic_years(learning_unit_to_edit, new_academic_year.year):
            new_luy = _duplicate_learning_unit_year(last_learning_unit_year, ac_year)
            result.append(_('learning_unit_created') % {
                'learning_unit': new_luy.acronym,
                'academic_year': new_luy.academic_year
            })

    return result


def _check_extend_partim(last_learning_unit_year, new_academic_year):
    if not new_academic_year:  # If there is no selected academic_year, we take the maximal value
        new_academic_year = AcademicYear.objects.get(year=compute_max_academic_year_adjournment() + 1)

    lu_parent = last_learning_unit_year.parent
    if last_learning_unit_year.is_partim() and lu_parent:
        if _get_actual_end_year(lu_parent.learning_unit) < new_academic_year.year:
            raise IntegrityError(
                _('parent_greater_than_partim') % {'partim_end_year': new_academic_year,
                                                   'lu_parent': lu_parent.acronym}
            )


def _update_end_year_field(lu, year):
    lu.end_year = year
    lu.save()
    return _('learning_unit_updated') % {'learning_unit': lu.acronym}


def _duplicate_learning_unit_year(old_learn_unit_year, new_academic_year):
    duplicated_luy = update_related_object(old_learn_unit_year, 'academic_year', new_academic_year)
    duplicated_luy.attribution_procedure = None
    duplicated_luy.learning_container_year = _duplicate_learning_container_year(duplicated_luy, new_academic_year)
    duplicated_luy.save()
    return duplicated_luy


def _duplicate_learning_container_year(new_learn_unit_year, new_academic_year):
    duplicated_lcy = _get_or_create_container_year(new_learn_unit_year, new_academic_year)
    _duplicate_learning_component_year(duplicated_lcy, new_learn_unit_year)
    duplicated_lcy.save()
    return duplicated_lcy


def _get_or_create_container_year(new_learn_unit_year, new_academic_year):
    queryset = LearningContainerYear.objects.filter(
        academic_year=new_academic_year,
        learning_container=new_learn_unit_year.learning_unit.learning_container
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
                _('Entity_not_exist') % {
                    'entity_acronym': entity_versions.last().acronym,
                    'academic_year': new_academic_year
                })
        update_related_object(entity_container_y, 'learning_container_year', new_lcy)


def _duplicate_learning_component_year(new_learn_container_year, new_learn_unit_year):
    for old_component in learning_component_year.find_by_learning_container_year(new_learn_container_year.copied_from):
        new_component = update_related_object(old_component, 'learning_container_year', new_learn_container_year)
        _duplicate_learning_class_year(new_component)
        _duplicate_learning_unit_component(new_component, new_learn_unit_year)
        _duplicate_entity_component_year(new_component)


def _duplicate_entity_component_year(new_component):
    new_learning_container = new_component.learning_container_year
    for old_entity_comp_year in EntityComponentYear.objects.filter(learning_component_year=new_component.copied_from):
        old_entity_container = old_entity_comp_year.entity_container_year
        new_entity_container_year = EntityContainerYear.objects.get(
            learning_container_year=new_learning_container,
            entity=old_entity_container.entity,
            type=old_entity_container.type
        )

        new_entity_component_year = update_related_object(old_entity_comp_year,
                                                          'entity_container_year',
                                                          new_entity_container_year)
        new_entity_component_year.learning_component_year = new_component
        new_entity_component_year.save()


def _duplicate_learning_unit_component(new_component, new_learn_unit_year):
    for old_learn_unit_comp in learning_unit_component.search(a_learning_component_year=new_component.copied_from,
                                                              a_learning_unit_year=new_learn_unit_year.copied_from):
        new_luc = update_related_object(old_learn_unit_comp, 'learning_unit_year', new_learn_unit_year)
        new_luc.learning_component_year = new_component
        new_luc.save()


def _duplicate_learning_class_year(new_component):
    for old_learning_class in learning_class_year.find_by_learning_component_year(new_component.copied_from):
        update_related_object(old_learning_class, 'learning_component_year', new_component)


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
            _('partim_greater_than_parent') % {
                'learning_unit': learning_unit_to_edit.acronym,
                'partim': partim.acronym,
                'year': new_academic_year
            }
        )


def _get_actual_end_year(learning_unit_to_edit):
    return learning_unit_to_edit.end_year or compute_max_academic_year_adjournment() + 1


def _get_new_end_year(new_academic_year):
    return new_academic_year.year if new_academic_year else None


def _get_next_academic_years(learning_unit_to_edit, year):
    range_years = list(range(learning_unit_to_edit.end_year + 1, year + 1))
    return AcademicYear.objects.filter(year__in=range_years).order_by('year')


def filter_biennial(queryset, periodicity):
    result = queryset
    if periodicity != learning_unit_periodicity.ANNUAL:
        is_odd = periodicity == learning_unit_periodicity.BIENNIAL_ODD
        result = queryset.annotate(odd=F('year') % 2).filter(odd=is_odd)
    return result


def update_learning_unit_year_with_report(luy_to_update, fields_to_update, with_report=True):

    _update_learning_unit_year(luy_to_update, fields_to_update)

    if with_report:
        fields_not_to_report = ("is_vacant", "type_declaration_vacant", "attribution_procedure")
        _apply_report(_update_learning_unit_year, luy_to_update, fields_to_update,
                      fields_to_exclude=fields_not_to_report)


def update_learning_unit_year_entities_with_report(luy_to_update, entities_by_type_to_update, with_report=True):
    _update_learning_unit_year_entities(luy_to_update, entities_by_type_to_update)

    if with_report:
        _apply_report(_update_learning_unit_year_entities, luy_to_update, entities_by_type_to_update)


def _apply_report(method_of_update, base_luy, *args, **kwargs):
    for luy in base_luy.find_gt_learning_units_year():
        method_of_update(luy, *args, **kwargs)


def _update_learning_unit_year(luy_to_update, fields_to_update, fields_to_exclude=()):
    if luy_to_update.is_in_proposal():
        raise IntegrityError(
            _("learning_unit_in_proposal_cannot_save") % {
                'luy': luy_to_update.acronym,
                'academic_year': luy_to_update.academic_year
            })
    update_instance_model_from_data(luy_to_update.learning_unit, fields_to_update)
    update_instance_model_from_data(luy_to_update.learning_container_year, fields_to_update, exclude=fields_to_exclude)
    update_instance_model_from_data(luy_to_update, fields_to_update, exclude=fields_to_exclude)


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
    if type_entity in ENTITY_TYPES_VOLUME:
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
