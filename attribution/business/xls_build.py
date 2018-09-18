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

from django.utils.translation import ugettext_lazy as _

from osis_common.document import xls_build
from attribution.business import attribution_charge_new
from base.business.learning_unit import get_entity_acronym
from base.business.xls import get_name_or_username

WORKSHEET_TITLE = 'learning_units'
XLS_FILENAME = 'learning_units_and_attributions_filename'
XLS_DESCRIPTION = "attribution_list"

ATTRIBUTION_TITLES = [str(_('tutor')), str(_('function')), str(_('substitute')), str(_('LECTURING')),
                      str(_('PRACTICAL_EXERCISES')), str(_('start_year')), str(_('duration'))]

LEARNING_UNIT_TITLES = [
    str(_('academic_year_small')),
    str(_('code')),
    str(_('title')),
    str(_('type')),
    str(_('subtype')),
    str(_('requirement_entity_small')),
    str(_('allocation_entity_small')),
    str(_('credits')),
    str(_('active_title'))
]


def prepare_xls_content(found_learning_units):
    res = []
    for learning_unit_yr in found_learning_units:
        for key, value in learning_unit_yr.attribution_charge_news.items():
            line_by_attribution = extract_xls_data_from_learning_unit(learning_unit_yr)
            line_by_attribution.append(value.get('person'))
            line_by_attribution.append(xls_build.translate(value.get('function')))
            line_by_attribution.append(value.get('substitute'))
            line_by_attribution.append(value.get('LECTURING'))
            line_by_attribution.append(value.get('PRACTICAL_EXERCISES'))
            line_by_attribution.append(value.get('start_year'))
            line_by_attribution.append(value.get('duration'))
            res.append(line_by_attribution)
    return res


def prepare_xls_parameters_list(user, working_sheets_data):
    return {xls_build.LIST_DESCRIPTION_KEY: _(XLS_DESCRIPTION),
            xls_build.FILENAME_KEY: _(XLS_FILENAME),
            xls_build.USER_KEY: get_name_or_username(user),
            xls_build.WORKSHEETS_DATA:
                [{xls_build.CONTENT_KEY: working_sheets_data,
                  xls_build.HEADER_TITLES_KEY: _prepare_titles(),
                  xls_build.WORKSHEET_TITLE_KEY: _(WORKSHEET_TITLE),
                  }
                 ]}


def _prepare_titles():
    titles = LEARNING_UNIT_TITLES.copy()
    for title in ATTRIBUTION_TITLES:
        titles.append(title)
    return titles


def create_xls_attribution(user, found_learning_units, filters):
    for learning_unit_yr in found_learning_units:
        learning_unit_yr.attribution_charge_news = attribution_charge_new\
            .find_attribution_charge_new_by_learning_unit_year(learning_unit_year=learning_unit_yr)

    working_sheets_data = prepare_xls_content(found_learning_units)
    return xls_build.generate_xls(prepare_xls_parameters_list(user, working_sheets_data), filters)


def extract_xls_data_from_learning_unit(learning_unit_yr):
    return [
        learning_unit_yr.academic_year.name, learning_unit_yr.acronym, learning_unit_yr.complete_title,
        xls_build.translate(learning_unit_yr.learning_container_year.container_type)
        # FIXME Condition to remove when the LearningUnitYear.learning_continer_year_id will be null=false
        if learning_unit_yr.learning_container_year else "",
        xls_build.translate(learning_unit_yr.subtype),
        get_entity_acronym(learning_unit_yr.entities.get('REQUIREMENT_ENTITY')),
        get_entity_acronym(learning_unit_yr.entities.get('ALLOCATION_ENTITY')),
        learning_unit_yr.credits, xls_build.translate(learning_unit_yr.status)
    ]
