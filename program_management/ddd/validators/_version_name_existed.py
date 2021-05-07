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
from base.ddd.utils.business_validator import BusinessValidator
from program_management.ddd.domain.exception import VersionNameExistsInPast


class VersionNameExistedValidator(BusinessValidator):

    def __init__(self, working_year: int, offer_acronym: str, version_name: str, transition_name: str):
        super().__init__()
        self.working_year = working_year
        self.version_name = version_name
        self.offer_acronym = offer_acronym
        self.transition_name = transition_name

    def validate(self):
        from program_management.ddd.domain.service.get_last_existing_version_name import GetLastExistingVersion
        last_version_identity = GetLastExistingVersion().get_last_existing_version_identity(
            self.version_name,
            self.offer_acronym,
            self.transition_name
        )
        if last_version_identity and last_version_identity.year < self.working_year:
            raise VersionNameExistsInPast(last_version_identity.version_name)
