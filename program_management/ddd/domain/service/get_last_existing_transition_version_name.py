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
from typing import Union

from django.db.models import F

from osis_common.ddd import interface
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity, NOT_A_TRANSITION
from program_management.models.education_group_version import EducationGroupVersion


class GetLastExistingTransitionVersion(interface.DomainService):

    @classmethod
    def get_last_existing_transition_version_identity(
            cls,
            version_name: str,
            offer_acronym: str,
            year: int
    ) -> Union[ProgramTreeVersionIdentity, None]:
        group_version = EducationGroupVersion.objects.filter(
            version_name=version_name,
            root_group__acronym=offer_acronym,
            offer__academic_year__year=year
        ).exclude(
            transition_name=NOT_A_TRANSITION
        ).annotate(
            year=F('offer__academic_year__year'),
            offer_acronym=F('offer__acronym'),
        ).values(
            'version_name',
            'year',
            'offer_acronym',
            'transition_name',
        ).order_by(
            'offer__academic_year__year'
        ).last()

        if not group_version:
            return

        return ProgramTreeVersionIdentity(
            offer_acronym=group_version['offer_acronym'],
            year=group_version['year'],
            version_name=group_version['version_name'],
            transition_name=group_version['transition_name'],
        )
