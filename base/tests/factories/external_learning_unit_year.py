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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime
import string

import factory.fuzzy
from factory.django import DjangoModelFactory

from base.models.learning_unit_year import MINIMUM_CREDITS, MAXIMUM_CREDITS
from base.tests.factories.entity import EntityFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonFactory


class ExternalLearningUnitYearFactory(DjangoModelFactory):
    class Meta:
        model = "base.ExternalLearningUnitYear"
        
    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyNaiveDateTime(datetime.datetime(2016, 1, 1),
                                          datetime.datetime(2017, 3, 1))
    external_acronym = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    external_credits = factory.fuzzy.FuzzyDecimal(MINIMUM_CREDITS, MAXIMUM_CREDITS, precision=0)

    learning_unit_year = factory.SubFactory(LearningUnitYearFactory)
    requesting_entity = factory.SubFactory(EntityFactory)
    author = factory.SubFactory(PersonFactory)
    co_graduation = True
