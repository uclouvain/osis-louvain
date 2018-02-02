##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase
from base.tests.factories.academic_year import AcademicYearFactory
from assistant.tests.factories.assistant_mandate import AssistantMandateFactory
from assistant.models import assistant_mandate

class TestAssistantMandateFactory(TestCase):

    def setUp(self):
        self.mandate = AssistantMandateFactory(
            academic_year=factory.SubFactory(AcademicYearFactory, year=datetime.date.today().year - 1))
        self.mandate2 = AssistantMandateFactory(
            academic_year=factory.SubFactory(AcademicYearFactory, year=datetime.date.today().year))
        self.researched_academic_year = self.mandate.academic_year

    def test_find_mandate_by_id(self):
        self.assertEqual(self.mandate, assistant_mandate.find_mandate_by_id(self.mandate.id))

    def test_find_by_academic_year(self):
        for current_mandate in assistant_mandate.find_by_academic_year(self.researched_academic_year):
            self.assertEqual(self.researched_academic_year, current_mandate.academic_year)
