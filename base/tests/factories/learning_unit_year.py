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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import factory
import factory.fuzzy
import string
import datetime
from django.conf import settings
from django.utils import timezone
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.academic_year import AcademicYearFakerFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit import LearningUnitFakerFactory
from factory.django import DjangoModelFactory
from faker import Faker
fake = Faker()

def _get_tzinfo():
    if settings.USE_TZ:
        return timezone.get_current_timezone()
    else:
        return None

class LearningUnitYearFactory(DjangoModelFactory):
    class Meta:
        model = "base.LearningUnitYear"

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    academic_year = factory.SubFactory(AcademicYearFactory)
    learning_unit = factory.SubFactory(LearningUnitFactory)
    learning_container_year = None #factory.SubFactory(LearningContainerYearFactory)
    changed = factory.fuzzy.FuzzyDateTime(datetime.datetime(2016, 1, 1, tzinfo=_get_tzinfo()),
                                          datetime.datetime(2017, 3, 1, tzinfo=_get_tzinfo()))
    acronym = factory.Sequence(lambda n: 'LUY-%d' % n)
    title = factory.Sequence(lambda n: 'Learning unit year - %d' % n)
    type = "C"
    credits = factory.fuzzy.FuzzyDecimal(99)
    decimal_scores = False
    team = False
    vacant = False
    in_charge = False


class LearningUnitYearFakerFactory(DjangoModelFactory):
    class Meta:
        model = "base.LearningUnitYear"

    external_id = factory.Sequence(lambda n: '10000000%02d' % n)
    academic_year = factory.SubFactory(AcademicYearFakerFactory)
    learning_unit = factory.SubFactory(LearningUnitFakerFactory)
    learning_container_year = None
    changed = fake.date_time_this_decade(before_now=True, after_now=True, tzinfo=_get_tzinfo())
    acronym = factory.Sequence(lambda n: 'LUY-%d' % n)
    title = factory.Sequence(lambda n: 'Learning unit year - %d' % n)
    type = "C"
    credits = factory.fuzzy.FuzzyDecimal(9)
    decimal_scores = False
    team = False
    vacant = False
    in_charge = False