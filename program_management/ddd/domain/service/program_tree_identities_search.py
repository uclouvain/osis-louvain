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

from django.db.models import F

from osis_common.ddd import interface
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity, NOT_A_TRANSITION
from program_management.models.education_group_version import EducationGroupVersion


class ProgramTreeIdentitiesSearch(interface.DomainService):

    @classmethod
    def search(
            cls, acronym: str, version_name: str, transition_name: str = NOT_A_TRANSITION
    ) -> List[ProgramTreeVersionIdentity]:
        values = EducationGroupVersion.objects.filter(
            version_name=version_name,
            offer__acronym=acronym,
            transition_name=transition_name,
        ).annotate(
            year=F('offer__academic_year__year'),
        ).values(
            'version_name',
            'offer__acronym',
            'transition_name',
            'year',
        )
        if values:
            return [
                ProgramTreeVersionIdentity(
                    version_name=value['version_name'],
                    offer_acronym=value['offer__acronym'],
                    year=value['year'],
                    transition_name=value['transition_name'],
                )
                for value in values
            ]
        return []
