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
from education_group.models.group_year import GroupYear
from osis_common.ddd import interface
from program_management.ddd.business_types import *
from program_management.ddd.repositories import load_tree


class ProgramTreeVersionRepository(interface.AbstractRepository):

    @classmethod
    def get(cls, entity_id: 'ProgramTreeVersionIdentity') -> 'ProgramTreeVersion':
        group_year = GroupYear.objects.filter(
            partial_acronym=entity_id.code, academic_year__year=entity_id.year
        ).select_related('education_group_version__education_group_year', 'academic_year')
        # FIXME :: implement load_version into this function ProgramTreeVersionRepository.get()
        return load_tree.load_version(
            group_year.education_group_version.education_group_year.acronym,
            group_year.academic_year.year,
            group_year.education_group_version.version_name,
            group_year.education_group_version.is_transition,
        )
