##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from base.models.enums.funding_codes import FundingCodes
from osis_common.ddd import interface


class Funding(interface.ValueObject):
    def __init__(
            self,
            can_be_funded: bool = False,
            funding_orientation: FundingCodes = None,
            can_be_international_funded: bool = False,
            international_funding_orientation: FundingCodes = None
    ):
        self.can_be_funded = can_be_funded or False
        self.funding_orientation = funding_orientation or ""
        self.can_be_international_funded = can_be_international_funded or False
        self.international_funding_orientation = international_funding_orientation or ""

    def __eq__(self, other):
        return self.can_be_funded == other.can_be_funded \
               and self.funding_orientation == other.funding_orientation \
               and self.can_be_international_funded == other.can_be_international_funded \
               and self.international_funding_orientation == other.international_funding_orientation

    def __hash__(self):
        return hash(
            str(self.can_be_funded)
            + self.funding_orientation.name
            + str(self.can_be_funded)
            + self.international_funding_orientation.name
        )
