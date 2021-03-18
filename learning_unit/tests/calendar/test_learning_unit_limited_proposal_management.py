##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.forms import model_to_dict
from django.test import TestCase

from base.models.academic_calendar import AcademicCalendar
from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from learning_unit.calendar.learning_unit_limited_proposal_management import \
    LearningUnitLimitedProposalManagementCalendar


class TestLearningUnitLimitedProposalManagementCalendarEnsureConsistencyUntilNPlus6(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        AcademicYearFactory.produce_in_future(cls.current_academic_year.year)

    def test_ensure_consistency_until_n_plus_6_assert_default_value(self):
        LearningUnitLimitedProposalManagementCalendar.ensure_consistency_until_n_plus_6()

        qs = AcademicCalendar.objects.filter(
            reference=AcademicCalendarTypes.LEARNING_UNIT_LIMITED_PROPOSAL_MANAGEMENT.name
        )

        self.assertEqual(qs.count(), 7)
        self.assertDictEqual(
            model_to_dict(qs.first(), fields=('title', 'reference', 'data_year', 'start_date', 'end_date')),
            {
                "title": "Gestion des propositions limitée",
                "reference": AcademicCalendarTypes.LEARNING_UNIT_LIMITED_PROPOSAL_MANAGEMENT.name,
                "data_year": self.current_academic_year.pk,
                # The first time that we can edit an 2020's object is in 2018 (=2020-2)
                "start_date": datetime.date(self.current_academic_year.year - 2, 9, 14),
                "end_date": datetime.date(self.current_academic_year.year, 9, 13),
            }
        )

    def test_ensure_consistency_until_n_plus_6_assert_idempotent(self):
        for _ in range(5):
            LearningUnitLimitedProposalManagementCalendar.ensure_consistency_until_n_plus_6()

        self.assertEqual(
            AcademicCalendar.objects.filter(
                reference=AcademicCalendarTypes.LEARNING_UNIT_LIMITED_PROPOSAL_MANAGEMENT.name
            ).count(),
            7
        )
