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
from base.models import academic_year
from education_group.ddd.business_types import *
from osis_common.ddd import interface


class CalculateEndPostponement(interface.DomainService):

    @classmethod
    def calculate_year_of_end_postponement(cls, training: 'Training') -> int:
        default_years_to_postpone = 6
        current_year = academic_year.starting_academic_year().year
        if training.end_year:
            default_years_to_postpone = training.end_year - training.year
        return current_year + default_years_to_postpone

    @classmethod
    def calculate_year_of_end_postponement_for_mini(cls, mini_training: 'MiniTraining') -> int:
        default_years_to_postpone = 6
        current_year = academic_year.starting_academic_year().year
        if mini_training.end_year:
            default_years_to_postpone = mini_training.end_year - mini_training.year
        return current_year + default_years_to_postpone
