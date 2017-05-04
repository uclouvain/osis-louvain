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
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.student import StudentFactory
from dissertation.tests.factories.dissertation_location import DissertationLocationFactory
from dissertation.tests.factories.dissertation_role import DissertationRoleFactory
from dissertation.tests.factories.proposition_dissertation import PropositionDissertationFactory
from dissertation.models import dissertation


class DissertationFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'dissertation.Dissertation'

    title = factory.Faker('text', max_nb_chars=150)
    author = factory.SubFactory(StudentFactory)
    status = factory.Iterator(dissertation.STATUS_CHOICES, getter=lambda c: c[0])
    defend_periode = factory.Iterator(dissertation.DEFEND_PERIODE_CHOICES, getter=lambda c: c[0])
    defend_year = factory.Faker('year')
    offer_year_start = factory.SubFactory(OfferYearFactory)
    proposition_dissertation = factory.SubFactory(PropositionDissertationFactory)
    description = factory.Faker('text', max_nb_chars=500)
    active = True
    creation_date = factory.Faker('date_time_this_decade', before_now=True, after_now=False, tzinfo=None)
    modification_date = factory.Faker('date_time_this_decade', before_now=True, after_now=False, tzinfo=None)
    location = factory.SubFactory(DissertationLocationFactory)

    dissertation_role = factory.RelatedFactory(DissertationRoleFactory, 'dissertation')
