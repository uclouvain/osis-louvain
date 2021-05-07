##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from typing import List

from base.ddd.utils.business_validator import BusinessValidator
from program_management.ddd.domain.exception import TransitionNameExistsInPast
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity, ProgramTreeVersion


class TransitionNameExistedValidator(BusinessValidator):

    def __init__(
            self,
            from_specific_version: ProgramTreeVersionIdentity,
            transition_name: str,
            all_versions: List[ProgramTreeVersion]
    ):
        super().__init__()
        self.from_specific_version = from_specific_version
        self.transition_name = transition_name
        self.all_transition_versions = [
            transition_version for transition_version in all_versions
            if transition_version.transition_name
        ]

    def validate(self):
        last_version_identity = self.get_last_existing_transition_version()
        if last_version_identity and last_version_identity.entity_identity.year < self.from_specific_version.year:
            raise TransitionNameExistsInPast(
                last_version_identity.transition_name
            )

    def get_last_existing_transition_version(self):
        return next(
            iter(
                sorted(
                    filter(
                        lambda transition_version:
                        transition_version.transition_name == self.transition_name
                        and transition_version.version_name == self.from_specific_version.version_name
                        and transition_version.entity_identity.offer_acronym == self.from_specific_version.offer_acronym
                        and transition_version.entity_identity.year < self.from_specific_version.year,
                        self.all_transition_versions,
                    ),
                    key=lambda transition_version: transition_version.entity_identity.year,
                    reverse=True
                )
            ), None
        )
