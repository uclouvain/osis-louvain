# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from collections import namedtuple

from django.db import Error

from base.business import education_group
from base.business.utils.model import model_to_dict_fk, compare_objects, update_object
from base.models.education_group_organization import EducationGroupOrganization
from base.models.education_group_year import EducationGroupYear
from base.models.hops import Hops

EDUCATION_GROUP_MAX_POSTPONE_YEARS = 6
FIELD_TO_EXCLUDE = ['id', 'uuid', 'external_id', 'academic_year', 'linked_with_epc', 'publication_contact_entity']
HOPS_FIELDS = ('ares_study', 'ares_graca', 'ares_ability')

FIELD_TO_EXCLUDE_IN_SET = ['id', 'external_id', 'education_group_year']

ReversePostponementConfig = namedtuple('ReversePostponementConfig', ['set_name', 'model', 'filter_field'])


class ConsistencyError(Error):
    def __init__(self, data, differences, *args, **kwargs):
        self.model = data['model']
        self.last_instance_updated = data['last_instance_updated']
        self.differences = differences
        super().__init__(*args, **kwargs)


def _postpone_m2m(education_group_year, postponed_egy, hops_values, fields_to_exclude=None):
    if fields_to_exclude is None:
        fields_to_exclude = []

    opts = education_group_year._meta
    for f in opts.many_to_many:
        if f.name in fields_to_exclude:
            continue
        m2m_cls = f.remote_field.through

        # Remove records of postponed_egy
        m2m_cls.objects.all().filter(education_group_year=postponed_egy).delete()

        # Recreate records
        for m2m_obj in m2m_cls.objects.all().filter(education_group_year_id=education_group_year):
            m2m_data_to_postpone = model_to_dict_fk(m2m_obj, exclude=['id', 'external_id', 'education_group_year'])
            m2m_cls(education_group_year=postponed_egy, **m2m_data_to_postpone).save()

    if hops_values and any(elem in HOPS_FIELDS and hops_values[elem] for elem in hops_values):
        _postpone_hops(hops_values, postponed_egy)


# TODO: Remove this function and use related service
def duplicate_education_group_year(old_education_group_year, new_academic_year,
                                   initial_dicts=None, hops_values=None, fields_to_exclude=None):
    if initial_dicts is None:
        initial_dicts = {}
    if fields_to_exclude is None:
        fields_to_exclude = FIELD_TO_EXCLUDE
    dict_new_value = model_to_dict_fk(old_education_group_year, exclude=fields_to_exclude)

    defaults_values = {x: v for x, v in dict_new_value.items() if not isinstance(v, list)}

    postponed_egy, created = EducationGroupYear.objects.get_or_create(
        education_group=old_education_group_year.education_group,
        academic_year=new_academic_year,
        # Create object without m2m relations
        defaults=defaults_values
    )

    # During create of new postponed object, we need to update only the m2m relations
    if created:
        # Postpone the m2m [languages / secondary_domains]
        _postpone_m2m(old_education_group_year, postponed_egy, hops_values)

    # During the update, we need to check if the postponed object has been modify
    else:
        dict_postponed_egy = model_to_dict_fk(postponed_egy, exclude=fields_to_exclude)
        differences = compare_objects(initial_dicts['dict_initial_egy'], dict_postponed_egy) \
            if initial_dicts['dict_initial_egy'] and dict_postponed_egy else {}

        if differences:
            raise ConsistencyError(
                {'model': EducationGroupYear, 'last_instance_updated': postponed_egy},
                differences
            )

        update_object(postponed_egy, dict_new_value)
        # Postpone the m2m [languages / secondary_domains]
        _postpone_m2m(old_education_group_year, postponed_egy, hops_values, fields_to_exclude=fields_to_exclude)

    if education_group.has_coorganization(old_education_group_year):
        duplicate_set(old_education_group_year, postponed_egy, initial_dicts.get('initial_sets_dict'))
    return postponed_egy


def duplicate_set(old_egy, education_group_year, initial_sets=None):
    if initial_sets is None:
        initial_sets = {}

    sets_to_duplicate = [
        ReversePostponementConfig('educationgrouporganization_set', EducationGroupOrganization, 'organization_id')
    ]
    for set_tuple in sets_to_duplicate:
        _update_and_check_consistency_of_set(education_group_year, old_egy, initial_sets, set_tuple)


def _update_and_check_consistency_of_set(education_group_year, old_egy, initial_sets, set_tuple):
    ids = []
    set_name, set_model, set_filter_field = set_tuple

    initial_set = initial_sets.get(set_name, {})
    egy_set = getattr(old_egy, set_name).all()
    sets_is_consistent = _check_consistency_of_all_set(education_group_year, initial_set, set_tuple)

    if not sets_is_consistent:
        raise ConsistencyError(
            {'model': set_model, 'last_instance_updated': education_group_year},
            {'consistency': ()}
        )

    for item_set in egy_set:
        dict_new_values = model_to_dict_fk(item_set, exclude=FIELD_TO_EXCLUDE_IN_SET)
        defaults_values = {x: v for x, v in dict_new_values.items() if not isinstance(v, list)}
        postponed_item, created = set_model.objects.get_or_create(
            education_group_year=education_group_year,
            defaults=defaults_values,
            **{set_filter_field: dict_new_values[set_filter_field]}
        )
        ids.append(postponed_item.id)

        if not created:
            _check_differences_and_update(dict_new_values, initial_set, postponed_item, set_tuple)

    set_model.objects.filter(education_group_year=education_group_year).exclude(id__in=ids).delete()


def _check_consistency_of_all_set(education_group_year, initial_set, set_tuple):
    set_name, _, set_filter_field = set_tuple
    postpone_set = getattr(education_group_year, set_name).all()
    initial_set = set(initial_set.keys())
    diff_orga = set(postpone_set.values_list(set_filter_field, flat=True)) - initial_set

    have_same_number = postpone_set.count() == len(initial_set)
    have_same_coorg = len(diff_orga) == 0

    return have_same_number and have_same_coorg


def _check_differences_and_update(dict_new_values, initial_set, postponed_item, set_tuple):
    set_name, set_model, set_filter_field = set_tuple

    dict_postponed_item = model_to_dict_fk(postponed_item, exclude=FIELD_TO_EXCLUDE_IN_SET)
    initial_item = initial_set.get(dict_postponed_item[set_filter_field])

    differences = compare_objects(initial_item, dict_postponed_item) \
        if initial_item and dict_postponed_item else {}
    if differences:
        raise ConsistencyError(
            {'model': set_model, 'last_instance_updated': postponed_item},
            differences
        )
    update_object(postponed_item, dict_new_values)


def _postpone_hops(hops_values, postponed_egy):
    Hops.objects.update_or_create(education_group_year=postponed_egy,
                                  defaults={'ares_study': hops_values['ares_study'],
                                            'ares_graca': hops_values['ares_graca'],
                                            'ares_ability': hops_values['ares_ability']})
