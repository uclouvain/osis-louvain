##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

from assessments.models.enums import score_sheet_address_choices
from base.tests.factories.education_group import EducationGroupFactory
from reference.tests.factories.country import CountryFactory


class ScoreSheetAddressFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'assessments.ScoreSheetAddress'

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyNaiveDateTime(datetime.datetime(2016, 1, 1),
                                          datetime.datetime(2017, 3, 1))
    education_group = factory.SubFactory(EducationGroupFactory)
    entity_address_choice = factory.Iterator(score_sheet_address_choices.CHOICES, getter=operator.itemgetter(0))
    recipient = factory.Sequence(lambda n: 'Recipient - %d' % n)
    location = factory.Sequence(lambda n: 'Location - %d' % n)
    postal_code = factory.Sequence(lambda n: 'Postal code - %d' % n)
    city = factory.Sequence(lambda n: 'City - %d' % n)
    country = factory.SubFactory(CountryFactory)
    phone = factory.Sequence(lambda n: 'Phone - %d' % n)
    fax = factory.Sequence(lambda n: 'Fax - %d' % n)
    email = factory.Sequence(lambda n: 'Email - %d' % n)
