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
from django.db import transaction

from program_management.ddd.domain.program_tree_version import ProgramTreeVersion
from program_management.ddd.repositories import persist_tree
from program_management.models.education_group_version import EducationGroupVersion


@transaction.atomic
def persist(program_tree_version: ProgramTreeVersion) -> None:
    persist_tree.persist(program_tree_version.tree)
    new_education_group_version = EducationGroupVersion(
        version_name=program_tree_version.version_name,
        title_fr=program_tree_version.title_fr,
        title_en=program_tree_version.title_en,
        offer=education_group_year,
        is_transition=program_tree_version.is_transition,
        root_group=new_groupyear
    )
    new_education_group_version.save()
