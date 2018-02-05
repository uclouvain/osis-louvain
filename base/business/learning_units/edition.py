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
import uuid
from copy import copy

from django.db import IntegrityError, transaction
from django.db.models import F
from django.utils.translation import ugettext_lazy as _

from base.business.learning_unit import compute_max_academic_year_adjournment
from base.business.learning_unit_deletion import delete_from_given_learning_unit_year, \
    check_learning_unit_year_deletion
from base.models import entity_container_year, learning_component_year, learning_class_year, learning_unit_component
from base.models.academic_year import AcademicYear
from base.models.entity_component_year import EntityComponentYear
from base.models.entity_version import EntityVersion
from base.models.enums import learning_unit_periodicity, learning_unit_year_subtypes
from base.models.learning_container_year import LearningContainerYear
from base.models.learning_unit_year import LearningUnitYear


def edit_learning_unit_end_date(learning_unit_to_edit, new_academic_year):
    result = []

    new_end_year = _get_new_end_year(new_academic_year)
    end_year = _get_actual_end_year(learning_unit_to_edit)

    if not new_academic_year:  # If there is no selected academic_year, we take the maximal value
        new_academic_year = AcademicYear.objects.get(year=compute_max_academic_year_adjournment())

    if new_academic_year.year > end_year:
        result.extend(extend_learning_unit(learning_unit_to_edit, new_academic_year))
    elif new_academic_year.year < end_year:
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

    with transaction.atomic():
        for ac_year in _get_next_academic_years(learning_unit_to_edit, new_academic_year.year):
            new_luy = _update_academic_year_for_learning_unit_year(last_learning_unit_year, ac_year)
            result.append(_('learning_unit_created') % {
                'learning_unit': new_luy.acronym,
                'academic_year': new_luy.academic_year
            })

    return result


def _check_extend_partim(last_learning_unit_year, new_academic_year):
    lu_parent = last_learning_unit_year.parent
    if last_learning_unit_year.subtype == 'PARTIM' and lu_parent:
        if _get_actual_end_year(lu_parent.learning_unit) < new_academic_year.year:
            raise IntegrityError(
                _('parent_greater_than_partim') % {'partim_end_year': new_academic_year,
                                                   'lu_parent': lu_parent.acronym}
                                 )


def _update_end_year_field(lu, year):
    lu.end_year = year
    lu.save()
    return _('learning_unit_updated') % {'learning_unit': lu.acronym}


def _duplicate_object(obj):
    obj = copy(obj)
    obj.pk = None
    obj.uuid = uuid.uuid4()
    return obj


def _update_academic_year_for_learning_unit_year(luy, new_academic_year):
    old_luy_pk = luy.pk
    duplicated_luy = _update_related_row(luy, 'academic_year', new_academic_year)
    duplicated_luy.attribution_procedure = None
    duplicated_luy.learning_container_year = _update_learning_container_year(duplicated_luy,
                                                                             new_academic_year,
                                                                             old_luy_pk)
    duplicated_luy.save()
    return duplicated_luy


def _update_learning_container_year(luy, new_academic_year, old_luy_pk):
    old_lcy_pk = luy.learning_container_year.pk
    return _get_or_duplication_container(luy, new_academic_year, old_lcy_pk, old_luy_pk)


def _get_or_duplication_container(luy, new_academic_year, old_lcy_pk, old_luy_pk):
    queryset = LearningContainerYear.objects.filter(
        academic_year=new_academic_year,
        learning_container=luy.learning_unit.learning_container
    )
    # Sometimes, the container already exists, we can directly use it and its entitycontaineryear
    if not queryset.exists():
        duplicated_lcy = _update_related_row(luy.learning_container_year, 'academic_year', new_academic_year)
        duplicated_lcy.is_vacant = False
        duplicated_lcy.type_declaration_vacant = None

        _update_entity_container_year(old_lcy_pk, duplicated_lcy, new_academic_year)
    else:
        duplicated_lcy = queryset.get()

    _update_learning_component_year(old_lcy_pk, duplicated_lcy, old_luy_pk, luy)
    duplicated_lcy.save()
    return duplicated_lcy


def _update_entity_container_year(old_lcy_pk, new_lcy, new_academic_year):
    for entity_container_y in entity_container_year.search(learning_container_year=old_lcy_pk):
        entity_versions = EntityVersion.objects.entity(entity_container_y.entity)
        if not entity_versions.current(new_academic_year.end_date).exists():
            raise IntegrityError(
                _('Entity_not_exist') % {
                    'entity_acronym': entity_versions.last().acronym,
                    'academic_year': new_academic_year
                })
        duplicate_ecy = _update_related_row(entity_container_y, 'learning_container_year', new_lcy)

        _update_entity_component_year(duplicate_ecy, entity_container_y)


def _update_entity_component_year(duplicate_ecy, entity_container_y):
    for entity_component_year in EntityComponentYear.objects.filter(entity_container_year=entity_container_y):
        _update_related_row(entity_component_year, 'entity_container_year', duplicate_ecy)


def _update_learning_component_year(old_lcy_pk, new_lcy, old_luy_pk, luy):
    for component in learning_component_year.find_by_learning_container_year(old_lcy_pk):
        old_component_pk = component.pk
        component = _update_related_row(component, 'learning_container_year', new_lcy)
        _update_learning_class_year(old_component_pk, component)
        _update_learning_unit_component(old_component_pk, old_luy_pk, component, luy)


def _update_learning_unit_component(old_component_pk, old_luy_pk, component, luy):
    for luc in learning_unit_component.search(a_learning_component_year=old_component_pk,
                                              a_learning_unit_year=old_luy_pk):
        new_luc = _update_related_row(luc, 'learning_unit_year', luy)
        new_luc.learning_component_year = component
        new_luc.save()


def _update_learning_class_year(old_component_pk, new_component):
    for learning_class in learning_class_year.find_by_learning_component_year(old_component_pk):
        _update_related_row(learning_class, 'learning_component_year', new_component)


def _update_related_row(row, attribute_name, new_value):
    duplicated_row = _duplicate_object(row)
    setattr(duplicated_row, attribute_name, new_value)
    duplicated_row.save()
    return duplicated_row


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
    return learning_unit_to_edit.end_year or compute_max_academic_year_adjournment()


def _get_new_end_year(new_academic_year):
    return new_academic_year.year if new_academic_year else None


def _get_next_academic_years(learning_unit_to_edit, year):
    range_years = list(range(learning_unit_to_edit.end_year + 1, year + 1))
    queryset = AcademicYear.objects.filter(year__in=range_years).order_by('year')
    return filter_biennial(queryset, learning_unit_to_edit.periodicity)


def filter_biennial(queryset, periodicity):
    result = queryset
    if periodicity != learning_unit_periodicity.ANNUAL:
        is_odd = periodicity == learning_unit_periodicity.BIENNIAL_ODD
        result = queryset.annotate(odd=F('year') % 2).filter(odd=is_odd)
    return result
