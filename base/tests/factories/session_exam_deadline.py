##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
import datetime
import operator
import string

import factory
import factory.fuzzy
from django.conf import settings
from django.utils import timezone

from base.models.enums import number_session
from utils.helpers import get_tzinfo

from .offer_enrollment import OfferEnrollmentFactory


class SessionExamDeadlineFactory(factory.DjangoModelFactory):
    class Meta:
        model = "base.SessionExamDeadline"

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyDateTime(datetime.datetime(2016, 1, 1, tzinfo=get_tzinfo()),
                                          datetime.datetime(2017, 3, 1, tzinfo=get_tzinfo()))
    deadline = factory.fuzzy.FuzzyDate(datetime.datetime(2016, 1, 1, tzinfo=get_tzinfo()),
                                       datetime.datetime(2017, 3, 1, tzinfo=get_tzinfo()))
    deadline_tutor = factory.fuzzy.FuzzyInteger(10) # max 10 days delta
    number_session = factory.Iterator(number_session.NUMBERS_SESSION, getter=operator.itemgetter(0))
    offer_enrollment = factory.SubFactory(OfferEnrollmentFactory)
