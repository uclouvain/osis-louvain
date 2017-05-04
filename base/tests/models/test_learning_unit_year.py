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
from django.test import TestCase
from django.utils import timezone
from attribution.models import attribution
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory


def create_learning_unit_year(acronym, title, academic_year):
    learning_unit = LearningUnitFactory(acronym=acronym, title=title, start_year=2010)
    return LearningUnitYearFactory(acronym=acronym,
                                   title=title,
                                   academic_year=academic_year,
                                   learning_unit=learning_unit)


class LearningUnitYearTest(TestCase):
    def setUp(self):
        self.tutor = TutorFactory()
        self.academic_year = AcademicYearFactory(year=timezone.now().year)
        self.learning_unit_year = LearningUnitYearFactory(acronym="LDROI1004", title="Juridic law courses",
                                                          academic_year=self.academic_year)

    def test_find_by_tutor_with_none_argument(self):
        self.assertEquals(attribution.find_by_tutor(None), None)
