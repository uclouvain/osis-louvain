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
from typing import List, Dict

from django.contrib.postgres.aggregates import ArrayAgg
from django.db.models import F, Q

from base.models.prerequisite import Prerequisite as PrerequisiteModel
from osis_common.ddd import interface
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity


class CheckIfPrerequisitesExists(interface.DomainService):

    @staticmethod
    def has_or_is_prerequisites(node_identities: List['NodeIdentity']) -> Dict['NodeIdentity', 'ProgramTreeVersionIdentity']:
        assert len({n.year for n in node_identities}) == 1, "Impossible to work with prerequisites in different years"

        year = node_identities[0].year
        queryset = PrerequisiteModel.objects.annotate(
            is_a_prerequisite_of=ArrayAgg('prerequisite__learning_unit_year__acronym'),
        ).filter(
            Q(
                education_group_version__root_group__partial_acronym__in=set(n.code for n in node_identities),
                education_group_version__root_group__academic_year__year=year,
            ) | Q(
                prerequisite__learning_unit_year__acronym__in=...
            )
        ).annotate(
            root_code=F('education_group_version__root_group__partial_acronym'),
            learning_unit_code=F('learning_unit_year__acronym'),
            version_name=F('education_group_version__version_name'),
            is_transition=F('education_group_version__is_transition'),
            offer_acronym=F('education_group_version__offer__acronym'),
        )

        result = {}

        for row in queryset:
            node_identity = NodeIdentity(code=row['root_code'], year=year)
            version_identity = ProgramTreeVersionIdentity(
                offer_acronym=row['offer_acronym'],
                version_name=row['version_name'],
                is_transition=row['is_transition'],
                year=year,
            )
            result[node_identity]: version_identity

        return result

    @staticmethod
    def is_prerequisite(node_identities: List['NodeIdentity']) -> Dict['NodeIdentity', 'ProgramTreeVersionIdentity']:
        assert len({n.year for n in node_identities}) == 1, "Impossible to work with prerequisites in different years"

        year = node_identities[0].year
        queryset = PrerequisiteModel.objects.filter(
            education_group_version__root_group__partial_acronym__in=set(n.code for n in node_identities),
            education_group_version__root_group__academic_year__year=year,
        ).annotate(
            root_code=F('education_group_version__root_group__partial_acronym'),
            learning_unit_code=F('learning_unit_year__acronym'),
            version_name=F('education_group_version__version_name'),
            is_transition=F('education_group_version__is_transition'),
            offer_acronym=F('education_group_version__offer__acronym'),
        )

        result = {}

        for row in queryset:
            node_identity = NodeIdentity(code=row['root_code'], year=year)
            version_identity = ProgramTreeVersionIdentity(
                offer_acronym=row['offer_acronym'],
                version_name=row['version_name'],
                is_transition=row['is_transition'],
                year=year,
            )
            result[node_identity]: version_identity

        return result
