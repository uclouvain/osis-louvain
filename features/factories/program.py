# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
import itertools
import random
from typing import Dict, List

from base.models.academic_year import current_academic_year
from base.models.authorized_relationship import AuthorizedRelationship
from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory


class ProgramGenerators:
    def __init__(self):
        self.trainings = EducationGroupYear.objects.filter(
            academic_year=current_academic_year()
        ).select_related("education_group_type")
        self.learning_unit_years = list(LearningUnitYear.objects.filter(
            academic_year=current_academic_year()
        ))

        self.relationships = self._load_authorized_relationships()
        self.create_structure()

    def _load_authorized_relationships(self) -> Dict[EducationGroupType, List[AuthorizedRelationship]]:
        all_relationships = AuthorizedRelationship.objects.all().order_by(
            "parent_type"
        ).select_related(
            "parent_type",
            "child_type"
        )
        result = {}
        relationships_group_by_parent = itertools.groupby(all_relationships, lambda relationship: relationship.parent_type)
        for parent, parent_relationships in relationships_group_by_parent:
            result[parent] = list(parent_relationships)
        return result

    def create_structure(self):
        for training in self.trainings:
            self._create_structure(training)

    def _create_structure(self, education_group_year_obj: EducationGroupYear, level=3):
        if level <= 0 and education_group_year_obj.education_group_type.learning_unit_child_allowed:
            number_lu = random.randint(3, 5)
            luys = random.choices(self.learning_unit_years, k=number_lu)
            for luy in luys:
                GroupElementYearChildLeafFactory(
                    parent=education_group_year_obj,
                    child_leaf=luy
                )

        relationships = self.relationships.get(education_group_year_obj.education_group_type, [])
        for relationship in relationships:
            generate = bool(random.randint(0, 1))
            if not (relationship.min_count_authorized == 1 or generate):
                continue
            grp = GroupElementYearFactory(
                parent=education_group_year_obj,
                child_branch__education_group_type=relationship.child_type,
                child_branch__management_entity=education_group_year_obj.management_entity
            )
            self._create_structure(grp.child_branch, level=level-1)

