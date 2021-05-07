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
from typing import Union

from django.db.models import Q

from osis_common.ddd import interface
from program_management.models.education_group_version import EducationGroupVersion


class GetNextVersionIfExists(interface.DomainService):

    @classmethod
    def get_next_transition_version_year(
            cls,
            initial_end_year: int,
            end_year: int,
            offer_acronym: str,
            version_name: str,
    ) -> Union[int, None]:
        next_transitions = EducationGroupVersion.objects.filter(
            Q(root_group__academic_year__year__gt=initial_end_year) &
            Q(root_group__academic_year__year__lte=end_year),
            version_name=version_name,
            offer__acronym=offer_acronym,
        ).exclude(
            Q(transition_name__isnull=True) | Q(transition_name='')
        ).order_by('root_group__academic_year__year')
        if next_transitions:
            return next_transitions.first().offer.academic_year.year
        return None
