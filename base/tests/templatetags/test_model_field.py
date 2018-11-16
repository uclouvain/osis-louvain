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
from django.test import TestCase
from django.test.utils import override_settings

from base.templatetags.model_field import get_attribute
from base.models.enums import quadrimesters
from base.tests.factories.learning_unit_year import LearningUnitYearFactory

TITLE = 'title'


class LearningUnitTagTest(TestCase):
    def setUp(self):
        self.learning_unit_yr = LearningUnitYearFactory(specific_title=TITLE,
                                                        status=True,
                                                        professional_integration=True,
                                                        quadrimester=quadrimesters.Q1)

    @override_settings(LANGUAGES=[('fr-be', 'French'), ('en', 'English'), ], LANGUAGE_CODE='fr-be')
    def test_get_attribute(self):
        self.assertEqual(get_attribute(self.learning_unit_yr, 'specific_title'), TITLE)
        self.assertEqual(get_attribute(self.learning_unit_yr, 'professional_integration'), 'oui')
        self.assertEqual(get_attribute(self.learning_unit_yr, 'status'), 'Actif')
        self.assertEqual(get_attribute(self.learning_unit_yr, 'quadrimester'), quadrimesters.Q1)
