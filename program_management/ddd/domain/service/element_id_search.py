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
from typing import List, Dict, Union, Optional

from django.db.models import F

from education_group.ddd.domain.mini_training import MiniTrainingIdentity
from education_group.ddd.domain.training import TrainingIdentity
from education_group.models.group_year import GroupYear
from osis_common.ddd import interface
from program_management.models.element import Element

ElementId = int
Year = int
STANDARD = ''

class ElementIdByYearSearch(interface.DomainService):

    def search_from_element_ids(
            self,
            element_ids: List[ElementId]
    ) -> Dict[ElementId, Dict[Year, ElementId]]:
        """
        :return: Map associating elements ids given in parameter with these elements ids mapped by year :
        {
            <element_id>: {year: <element_id_of_year>}
        }
        """

        values_list = GroupYear.objects.filter(
            group__groupyear__element__pk__in=element_ids,
        ).annotate(
            element_id=F('element__pk'),
            year=F('academic_year__year'),
        ).values(
            'element_id',
            'group_id',
            'year',
        )

        grouped_by_group_id = {}
        for rec in values_list:
            grouped_by_group_id.setdefault(rec['group_id'], []).append(rec)

        result = {}
        for group_id, records in grouped_by_group_id.items():
            for record in records:
                element_id = record['element_id']
                result[element_id] = {
                    rec['year']: rec['element_id'] for rec in records
                }
        return result


class ElementIdSearch(interface.DomainService):

    def get_from_training_identity(self, training_identity: 'TrainingIdentity') -> Union[None, ElementId]:
        values = Element.objects.filter(
            group_year__educationgroupversion__version_name=STANDARD,
            group_year__educationgroupversion__is_transition=False,
            group_year__educationgroupversion__offer__acronym=training_identity.acronym,
            group_year__educationgroupversion__offer__academic_year__year=training_identity.year,
        ).values('pk')
        if values:
            return values[0]['pk']

    def get_from_mini_training_identity(self, mini_training_identity: 'MiniTrainingIdentity') -> Optional[ElementId]:
        values = Element.objects.filter(
            group_year__educationgroupversion__version_name=STANDARD,
            group_year__educationgroupversion__is_transition=False,
            group_year__educationgroupversion__offer__acronym=mini_training_identity.acronym,
            group_year__educationgroupversion__offer__academic_year__year=mini_training_identity.year,
        ).values('pk')
        if values:
            return values[0]['pk']
