##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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

from django.test import TestCase

from base.forms.learning_unit.educational_information import mail_reminder
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory

ACRONYM_2 = 'LBCTR1001'
ACRONYM_1 = 'LARKE1001'


class TestMethods(TestCase):
    def setUp(self):
        self.learning_unit_year1 = LearningUnitYearFakerFactory(acronym=ACRONYM_1)
        self.learning_unit_year2 = LearningUnitYearFakerFactory(acronym=ACRONYM_2)

    def test_get_acronyms_concatenation_blank_result(self):
        acronyms = mail_reminder._get_acronyms_concatenation([])
        self.assertEqual(acronyms, '')

    def test_get_acronyms_concatenation_one_element(self):
        acronyms = mail_reminder._get_acronyms_concatenation([self.learning_unit_year1])
        self.assertEqual(acronyms, ACRONYM_1)

    def test_get_acronyms_concatenation_several_element(self):
        acronyms = mail_reminder._get_acronyms_concatenation([self.learning_unit_year1, self.learning_unit_year2])
        self.assertEqual(acronyms, '{}, {}'.format(ACRONYM_1, ACRONYM_2))
