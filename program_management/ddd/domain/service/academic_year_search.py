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
from education_group.models.group_year import GroupYear
from program_management.ddd.domain.node import NodeIdentity


class ExistingAcademicYearSearch(interface.DomainService):
    def search_from_code(self, group_code: str) -> List[NodeIdentity]:
        years = GroupYear.objects.filter(
            group__groupyear__partial_acronym=group_code,
        ).annotate(
            year=F('academic_year__year'),
        ).values_list(
            'year',
            flat=True
        ).distinct()
        return [NodeIdentity(code=group_code, year=year) for year in sorted(years)]
