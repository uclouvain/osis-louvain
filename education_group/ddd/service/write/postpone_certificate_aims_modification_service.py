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
from typing import List

from education_group.ddd import command
from education_group.ddd.domain.exception import CertificateAimsCopyConsistencyException
from education_group.ddd.domain.service.conflicted_fields import ConflictedFields
from education_group.ddd.domain.training import TrainingIdentity
from education_group.ddd.repository.training import TrainingRepository
from education_group.ddd.service.write import update_certificate_aims_service, copy_certificate_aims_service
from program_management.ddd.domain.service.calculate_end_postponement import CalculateEndPostponement


def postpone_certificate_aims_modification(
        postpone_cmd: command.PostponeCertificateAimsCommand
) -> List['TrainingIdentity']:
    # GIVEN
    from_training_id = TrainingIdentity(
        acronym=postpone_cmd.postpone_from_acronym,
        year=postpone_cmd.postpone_from_year
    )
    conflicted_certificate_aims = ConflictedFields().get_conflicted_certificate_aims(from_training_id)

    # WHEN
    identities_created = [
        update_certificate_aims_service.update_certificate_aims(
            command.UpdateCertificateAimsCommand(
                acronym=postpone_cmd.postpone_from_acronym,
                year=postpone_cmd.postpone_from_year,
                aims=postpone_cmd.aims
            )
        )
    ]

    end_postponement_year = CalculateEndPostponement.calculate_end_postponement_year_training(
        identity=from_training_id,
        repository=TrainingRepository()
    )

    for year in range(from_training_id.year, end_postponement_year):
        if year + 1 in conflicted_certificate_aims:
            continue  # Do not copy info from year to N+1 because conflict detected

        identity_next_year = copy_certificate_aims_service.copy_certificate_aims_to_next_year(
            copy_cmd=command.CopyCertificateAimsToNextYearCommand(
                acronym=postpone_cmd.postpone_from_acronym,
                postpone_from_year=year
            )
        )

        # THEN
        if identity_next_year:
            identities_created.append(identity_next_year)

    if conflicted_certificate_aims:
        first_conflict_year = min(conflicted_certificate_aims)
        raise CertificateAimsCopyConsistencyException(first_conflict_year, ['certificate_aims'])
    return identities_created
