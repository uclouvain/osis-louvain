##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
import datetime
import factory
import factory.fuzzy
import string
import operator
from django.conf import settings
from django.utils import timezone
from base.models.offer_year_calendar import OfferYearCalendar

from base.tests.factories.session_examen import SessionExamFactory
from base.tests.factories.learning_unit_enrollment import LearningUnitEnrollment as LearningUnitEnrollmentFactory

from base.enums import exam_enrollment_justification_type as justification_types
from base.enums import exam_enrollment_state as enrollment_states


def _get_tzinfo():
    if settings.USE_TZ:
        return timezone.get_current_timezone()
    else:
        return None


class ExamEnrollmentFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'base.ExamEnrollment'

    external_id = factory.fuzzy.FuzzyText(length=10, chars=string.digits)
    changed = factory.fuzzy.FuzzyDateTime(datetime.datetime(2016, 1, 1, tzinfo=_get_tzinfo()),
                                          datetime.datetime(2017, 3, 1, tzinfo=_get_tzinfo()))

    score_draft = factory.fuzzy.FuzzyDecimal(99)
    score_reencoded = factory.fuzzy.FuzzyDecimal(99)
    score_final = factory.fuzzy.FuzzyDecimal(99)
    justification_draft = factory.Iterator(justification_types.JUSTIFICATION_TYPES, getter=operator.itemgetter(0))
    justification_reencoded = factory.Iterator(justification_types.JUSTIFICATION_TYPES, getter=operator.itemgetter(0))
    justification_final = factory.Iterator(justification_types.JUSTIFICATION_TYPES, getter=operator.itemgetter(0))
    session_exam = factory.SubFactory(SessionExamFactory)
    learning_unit_enrollment = factory.SubFactory(LearningUnitEnrollmentFactory)
    enrollment_state = factory.Iterator(enrollment_states.STATES, getter=operator.itemgetter(0))
