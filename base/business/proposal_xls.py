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
from base.business.learning_unit import get_entity_acronym
from base.business.xls import get_name_or_username

WORKSHEET_TITLE = 'Proposals'
XLS_FILENAME = 'Proposals'
XLS_DESCRIPTION = "List_proposals"

PROPOSAL_TITLES = [str(_('Req. Entity')), str(_('code')), str(_('title')), str(_('Title')),
                   str(_('Proposal type')), str(_('Proposal status')), str(_('Folder num.')),
                   str(_('Decision')), str(_('Periodicity')), str(_('credits')),
                   str(_('Alloc. Ent.')), str(_('Proposals date'))]


def prepare_xls_content(proposals):
    return [extract_xls_data_from_proposal(proposal) for proposal in proposals]


def extract_xls_data_from_proposal(proposal):
    return [get_entity_acronym(proposal.learning_unit_year.entities.get('REQUIREMENT_ENTITY')),
            proposal.learning_unit_year.acronym,
            proposal.learning_unit_year.complete_title,
            xls_build.translate(proposal.learning_unit_year.learning_container_year.container_type),
            xls_build.translate(proposal.type),
            xls_build.translate(proposal.state),
            proposal.folder,
            xls_build.translate(proposal.learning_unit_year.learning_container_year.type_declaration_vacant),
            xls_build.translate(proposal.learning_unit_year.periodicity),
            proposal.learning_unit_year.credits,
            get_entity_acronym(proposal.learning_unit_year.entities.get('ALLOCATION_ENTITY')),
            proposal.date.strftime('%d-%m-%Y')]


def prepare_xls_parameters_list(user, working_sheets_data):
    return {xls_build.LIST_DESCRIPTION_KEY: _(XLS_DESCRIPTION),
            xls_build.FILENAME_KEY: _(XLS_FILENAME),
            xls_build.USER_KEY: get_name_or_username(user),
            xls_build.WORKSHEETS_DATA:
                [{xls_build.CONTENT_KEY: working_sheets_data,
                  xls_build.HEADER_TITLES_KEY: PROPOSAL_TITLES,
                  xls_build.WORKSHEET_TITLE_KEY: _(WORKSHEET_TITLE),
                  }
                 ]}


def create_xls(user, proposals, filters):
    working_sheets_data = prepare_xls_content(proposals)
    return xls_build.generate_xls(
        xls_build.prepare_xls_parameters_list(working_sheets_data, configure_parameters(user)), filters)


def create_xls_proposal(user, proposals, filters):
    return xls_build.generate_xls(prepare_xls_parameters_list(prepare_xls_content(proposals),
                                                              configure_parameters(user)), filters)


def configure_parameters(user):
    return {xls_build.DESCRIPTION: XLS_DESCRIPTION,
            xls_build.USER: get_name_or_username(user),
            xls_build.FILENAME: XLS_FILENAME,
            xls_build.HEADER_TITLES: PROPOSAL_TITLES,
            xls_build.WS_TITLE: WORKSHEET_TITLE}
