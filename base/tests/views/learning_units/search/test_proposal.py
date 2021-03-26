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

from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from base.tests.factories.academic_calendar import generate_proposal_calendars_without_start_and_end_date
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.person import PersonWithPermissionsFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.views.learning_units.search.search_test_mixin import TestRenderToExcelMixin
from learning_unit.tests.factories.central_manager import CentralManagerFactory


class TestExcelGeneration(TestRenderToExcelMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = AcademicYearFactory.produce()
        cls.luys = LearningUnitYearFactory.create_batch(4)
        cls.url = reverse("learning_units_proposal")
        cls.get_data = {
            "academic_year": str(cls.luys[0].academic_year.id),
        }
        cls.tuples_xls_status_value_with_xls_method_function = (
            ("xls", "base.views.learning_units.search.common.create_xls_proposal"),
            ("xls_comparison", "base.views.learning_units.search.common.create_xls_proposal_comparison")
        )

        cls.person = PersonWithPermissionsFactory("can_access_learningunit")

    def setUp(self):
        self.client.force_login(self.person.user)


class TestListButtons(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_years = AcademicYearFactory.produce(number_past=0)
        luy = LearningUnitYearFactory(academic_year=academic_years[0])
        ProposalLearningUnitFactory(learning_unit_year=luy)
        cls.url = reverse("learning_units_proposal")
        cls.get_data = {
            "academic_year": str(luy.academic_year.id),
        }
        cls.person = CentralManagerFactory().person
        generate_proposal_calendars_without_start_and_end_date(academic_years)

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_presence_of_buttons(self):
        response = self.client.get(self.url, data=self.get_data)
        self.assertContains(response, 'id="btn_produce_xls_', count=6, status_code=200)

    def test_value_of_buttons(self):
        response = self.client.get(self.url, data=self.get_data)
        titles_expected = [
            _('List proposals'),
            _('List comparison LU / Proposal'),
            _('Configurable list of learning units'),
            _('List of learning units with one line per attribution'),
            _('List of learning units with educational information and specifications'),
            _('List of learning units with one line per training')
        ]
        for title in titles_expected:
            self.assertContains(response, title, count=1, status_code=200)
