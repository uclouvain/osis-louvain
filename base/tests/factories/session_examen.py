##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
import operator
import string

import factory.fuzzy
import factory.fuzzy

from base.models.enums import number_session as number_session_enum
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.offer_year import OfferYearFactory
from osis_common.utils.datetime import get_tzinfo


class SessionExamFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'base.SessionExam'

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyDateTime(datetime.datetime(2016, 1, 1, tzinfo=get_tzinfo()),
                                          datetime.datetime(2017, 3, 1, tzinfo=get_tzinfo()))
    number_session = factory.Iterator(number_session_enum.NUMBERS_SESSION, getter=operator.itemgetter(0))
    learning_unit_year = factory.SubFactory(LearningUnitYear)
    offer_year = factory.SubFactory(OfferYearFactory)
