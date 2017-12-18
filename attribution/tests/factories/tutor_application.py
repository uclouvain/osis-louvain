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
import string
import datetime
import factory
import factory.fuzzy
from faker import Faker
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.tutor import TutorFactory
from osis_common.utils.datetime import get_tzinfo
from attribution.models.enums import function

fake = Faker()


class TutorApplicationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = "attribution.TutorApplication"

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = fake.date_time_this_decade(before_now=True, after_now=True, tzinfo=get_tzinfo())
    function = factory.Iterator(function.FUNCTIONS, getter=lambda c: c[0])
    tutor = factory.SubFactory(TutorFactory)
    learning_container_year = factory.SubFactory(LearningContainerYearFactory)
    volume_lecturing = factory.fuzzy.FuzzyDecimal(99)
    volume_pratical_exercice = factory.fuzzy.FuzzyDecimal(99)
    last_changed = factory.fuzzy.FuzzyDateTime(datetime.datetime(2016, 1, 1, tzinfo=get_tzinfo()),
                                               datetime.datetime(2017, 3, 1, tzinfo=get_tzinfo()))
