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
import functools
import operator
from typing import List, Iterable, Dict

from django.db.models import Prefetch, Q

from base.models import teaching_material, learning_unit_year
from learning_unit.ddd.business_types import *
from learning_unit.ddd.domain import learning_unit_year_identity
from learning_unit.ddd.domain.teaching_material import TeachingMaterial


def bulk_load_teaching_materials(
        learning_unit_identities: Iterable['LearningUnitYearIdentity']
) -> Dict['LearningUnitYearIdentity', List['TeachingMaterial']]:
    result = dict()
    if not learning_unit_identities:
        return result

    identity_clauses = [_build_identity_clause(identity) for identity in learning_unit_identities]
    identity_filter_clause = functools.reduce(operator.or_, identity_clauses)

    prefetch_material_qs = teaching_material.TeachingMaterial.objects.only(
        'title',
        'mandatory',
        'learning_unit_year'
    ).order_by('order')
    qs = learning_unit_year.LearningUnitYear.objects.filter(
        identity_filter_clause
    ).prefetch_related(
        Prefetch("teachingmaterial_set", queryset=prefetch_material_qs, to_attr="materials")
    ).select_related("academic_year").only("academic_year", "acronym")
    for row in qs:
        lu_identity = learning_unit_year_identity.LearningUnitYearIdentity(
            code=row.acronym,
            year=row.academic_year.year
        )
        result[lu_identity] = [
            convert_teaching_material_db_row_to_domain_object(material) for material in row.materials
        ]
    return result


def convert_teaching_material_db_row_to_domain_object(
        db_object: teaching_material.TeachingMaterial) -> TeachingMaterial:
    return TeachingMaterial(title=db_object.title, is_mandatory=db_object.mandatory)


def _build_identity_clause(learning_unit_identity: 'LearningUnitYearIdentity') -> Q:
    return Q(acronym=learning_unit_identity.code, academic_year__year=learning_unit_identity.year)
