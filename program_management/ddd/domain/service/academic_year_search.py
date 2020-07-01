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

from education_group.models.group_year import GroupYear
from osis_common.ddd import interface
from program_management.ddd.business_types import *


class ExistingAcademicYearSearch(interface.DomainService):
    def search_from_node_identity(self, node_identity: 'NodeIdentity') -> List[int]:
        return GroupYear.objects.filter(
            group__groupyear__partial_acronym=node_identity.code,
            group__groupyear__academic_year__year=node_identity.year,
        ).annotate(
            year=F('academic_year__year'),
        ).values_list(
            'year',
            flat=True
        ).distinct()
