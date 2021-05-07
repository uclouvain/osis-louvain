# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
from program_management.ddd import command
from program_management.ddd.domain.program_tree_version import ProgramTreeVersion, ProgramTreeVersionIdentity, \
    ProgramTreeVersionIdentityBuilder
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.ddd.validators import validators_by_business_action


def check_transition_name(cmd: command.CheckTransitionNameCommand) -> None:
    from_specific_version = ProgramTreeVersionIdentityBuilder().build_specific_version(
        offer_acronym=cmd.from_offer_acronym,
        year=cmd.from_year,
        version_name=cmd.from_version_name,
    )
    all_versions = ProgramTreeVersionRepository().search(
        version_name=from_specific_version.version_name,
        offer_acronym=from_specific_version.offer_acronym,
    )
    validators_by_business_action.CheckTransitionNameValidatorList(
        from_specific_version=from_specific_version,
        new_transition_name=cmd.new_transition_name,
        all_versions=all_versions
    ).validate()
