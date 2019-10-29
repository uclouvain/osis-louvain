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
LEARNING_UNIT_YEARS = 'learning_unit_years'
PERSON = 'person'


def _update_responsible_data_with_new_learning_unit_yr(a_responsible_person, learning_unit_yr,
                                                       responsible_and_learning_unit_yr_list_param):
    responsible_and_learning_unit_yr_list = responsible_and_learning_unit_yr_list_param
    for a_known_responsible in responsible_and_learning_unit_yr_list:
        if a_known_responsible.get(PERSON) == a_responsible_person:
            learning_unit_yr_list_for_responsible = a_known_responsible.get(LEARNING_UNIT_YEARS)
            learning_unit_yr_list_for_responsible.append(learning_unit_yr)
            a_known_responsible[LEARNING_UNIT_YEARS] = learning_unit_yr_list_for_responsible
            return responsible_and_learning_unit_yr_list
    return responsible_and_learning_unit_yr_list


def _build_new_responsible_data(a_responsible_person, learning_unit_yr):
    return {PERSON: a_responsible_person,
            LEARNING_UNIT_YEARS: [learning_unit_yr]}


def _update_responsible_and_learning_unit_yr_list(learning_unit_yr, responsible_and_learning_unit_yr_list_param):
    responsible_and_learning_unit_yr_list = responsible_and_learning_unit_yr_list_param
    for responsible in learning_unit_yr.summary_responsibles:
        a_responsible_person = responsible.tutor.person
        if _is_new_responsible(responsible_and_learning_unit_yr_list, a_responsible_person):
            responsible_and_learning_unit_yr_list.append(
                _build_new_responsible_data(a_responsible_person, learning_unit_yr))
        else:
            responsible_and_learning_unit_yr_list = _update_responsible_data_with_new_learning_unit_yr(
                a_responsible_person, learning_unit_yr,
                responsible_and_learning_unit_yr_list)
    return responsible_and_learning_unit_yr_list


def _is_new_responsible(responsible_and_learning_unit_yr_list, a_person):
    for record_responsible_learning_units in responsible_and_learning_unit_yr_list:
        if record_responsible_learning_units.get(PERSON) == a_person:
            return False
    return True
