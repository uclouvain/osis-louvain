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
import datetime
from django.utils import timezone
from base.tests.factories.person import PersonFactory
from assistant.test.factories.reviewer import ReviewerFactory
from assistant.test.factories.assistant_mandate import AssistantMandateFactory
from assistant.models.enums import review_advice_choices
from assistant.models.enums import review_status

class ReviewFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'assistant.Review'

    reviewer = factory.SubFactory(ReviewerFactory)
    mandate =  factory.SubFactory(AssistantMandateFactory)
    advice = factory.Iterator(review_advice_choices.REVIEW_ADVICE_CHOICES, getter=lambda c: c[0])
    status = review_status.DONE
    if advice == review_advice_choices.CONDITIONAL:
        justification = factory.Faker('text', max_nb_chars=50)
    changed = datetime.date.today()
    confidential = factory.Faker('text', max_nb_chars=50)
    remark = factory.Faker('text', max_nb_chars=50)

