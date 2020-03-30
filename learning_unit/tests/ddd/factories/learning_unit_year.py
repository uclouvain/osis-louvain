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
import operator
import random

import factory.fuzzy

from base.models.enums.learning_unit_year_periodicity import PeriodicityEnum
from base.models.enums.proposal_type import ProposalType
from base.models.learning_unit_year import MAXIMUM_CREDITS, MINIMUM_CREDITS
from learning_unit.ddd.domain.learning_unit_year import LearningUnitYear


def generate_end_year(node):
    return node.year + 10


def generate_start_year(node):
    return node.year + 10


class LearningUnitYearFactory(factory.Factory):

    class Meta:
        model = LearningUnitYear
        abstract = False

    id = factory.Sequence(lambda n: n+1)
    acronym = factory.Sequence(lambda n: 'Code-%02d' % n)
    common_title_fr = factory.fuzzy.FuzzyText(length=240)
    specific_title_fr = factory.fuzzy.FuzzyText(length=240)
    common_title_en = factory.fuzzy.FuzzyText(length=240)
    specific_title_en = factory.fuzzy.FuzzyText(length=240)
    year = factory.fuzzy.FuzzyInteger(low=1999, high=2099)
    start_year = factory.LazyAttribute(generate_start_year)
    end_year = factory.LazyAttribute(generate_end_year)
    proposal_type = factory.Iterator(ProposalType.choices(), getter=operator.itemgetter(0))
    credits = factory.fuzzy.FuzzyDecimal(MINIMUM_CREDITS, MAXIMUM_CREDITS, precision=0)
    status = True
    periodicity = factory.Iterator(PeriodicityEnum.choices(), getter=operator.itemgetter(0))
