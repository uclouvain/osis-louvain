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
from django.utils import timezone
from base.tests.factories.person import PersonFactory
from dissertation.tests.factories.adviser import AdviserTeacherFactory
from dissertation.models.proposition_dissertation import PropositionDissertation


class PropositionDissertationFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'dissertation.PropositionDissertation'

    author = factory.SubFactory(AdviserTeacherFactory)
    creator = factory.SubFactory(PersonFactory)
    collaboration = factory.Iterator(PropositionDissertation.COLLABORATION_CHOICES, getter=lambda c: c[0])
    description = factory.Faker('text', max_nb_chars=500)
    level = factory.Iterator(PropositionDissertation.LEVELS_CHOICES, getter=lambda c: c[0])
    max_number_student = factory.fuzzy.FuzzyInteger(1, 50)
    title = factory.Faker('text', max_nb_chars=150)
    type = factory.Iterator(PropositionDissertation.TYPES_CHOICES, getter=lambda c: c[0])
    visibility = True
    active = True
    created_date = factory.Faker('date_time_this_year', before_now=True, after_now=False,
                                 tzinfo=timezone.get_current_timezone())
