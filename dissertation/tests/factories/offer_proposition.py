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
from base.tests.factories.offer import OfferFactory


class OfferPropositionFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'dissertation.OfferProposition'

    acronym = factory.Sequence(lambda n: 'OfferProposition {}'.format(n))
    offer = factory.SubFactory(OfferFactory)
    student_can_manage_readers = True
    adviser_can_suggest_reader = True
    evaluation_first_year = True
    validation_commission_exists = True
    start_visibility_proposition = factory.Faker('date_time_this_year', before_now=True, after_now=False, tzinfo=None)
    end_visibility_proposition = factory.Faker('date_time_this_year', before_now=False, after_now=True, tzinfo=None)
    start_visibility_dissertation = factory.Faker('date_time_this_year', before_now=True, after_now=False, tzinfo=None)
    end_visibility_dissertation = factory.Faker('date_time_this_year', before_now=False, after_now=True, tzinfo=None)
    start_jury_visibility = factory.Faker('date_time_this_year', before_now=True, after_now=False, tzinfo=None)
    end_jury_visibility = factory.Faker('date_time_this_year', before_now=False, after_now=True, tzinfo=None)
    start_edit_title = factory.Faker('date_time_this_year', before_now=True, after_now=False, tzinfo=None)
    end_edit_title = factory.Faker('date_time_this_year', before_now=False, after_now=True, tzinfo=None)
