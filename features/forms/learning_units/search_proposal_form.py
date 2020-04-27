# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from base.models.enums.proposal_type import ProposalType
from features.pages.learning_unit import pages


def fill_search_creation_proposal(page: pages.SearchProposalPage):
    proposal_type = ProposalType.CREATION.name
    page.proposal_type = proposal_type
    return {"proposal_type": proposal_type}


def fill_search_suppression_proposal(page: pages.SearchProposalPage):
    proposal_type = ProposalType.SUPPRESSION.name
    page.proposal_type = proposal_type
    return {"proposal_type": proposal_type}


def fill_search_modification_proposal(page: pages.SearchProposalPage):
    proposal_type = ProposalType.MODIFICATION.name
    page.proposal_type = proposal_type
    return {"proposal_type": proposal_type}
