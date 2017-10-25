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
from django.test import TestCase
from base.models import learning_unit
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.models.enums import learning_unit_year_subtypes
import datetime


def create_learning_unit(acronym, title):
    return LearningUnitFactory(acronym=acronym, title=title, start_year=2010)

class LearningUnitTest(TestCase):

    def test_create_learning_unit_with_start_year_higher_than_end_year(self):
        l_unit = LearningUnitFactory.build(start_year=2000, end_year=1999)
        with self.assertRaises(AttributeError):
            l_unit.save()

    def test_find_by_id(self):
        l_unit_1 = LearningUnitFactory()
        LearningUnitFactory()
        LearningUnitFactory()
        self.assertEqual(l_unit_1, learning_unit.find_by_id(l_unit_1.id))

    def test_find_by_ids(self):
        l_unit_1 = LearningUnitFactory()
        l_unit_2 = LearningUnitFactory()
        LearningUnitFactory()
        LearningUnitFactory()
        self.assertEqual(2, len( learning_unit.find_by_ids( (l_unit_1.id, l_unit_2.id) )))

    def test_search_by_acronym(self):
        LearningUnitFactory(acronym="LT49786")
        LearningUnitFactory()
        LearningUnitFactory()
        self.assertEqual(1, len(learning_unit.search(acronym="LT49786")))

    def test_get_partims_related(self):
        from base.business.learning_unit import get_partims_related
        current_year = datetime.date.today().year
        academic_year = AcademicYearFactory(year=current_year)
        l_container_year = LearningContainerYearFactory(academic_year=academic_year)
        l_container_year_2 = LearningContainerYearFactory(academic_year=academic_year)
        # Create learning unit year attached to learning container year
        learning_unit_year_1 = LearningUnitYearFactory(academic_year=academic_year,
                                                       learning_container_year=l_container_year,
                                                       subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(academic_year=academic_year,
                                learning_container_year=l_container_year,
                                subtype=learning_unit_year_subtypes.PARTIM)
        LearningUnitYearFactory(academic_year=academic_year,
                                learning_container_year=l_container_year,
                                subtype=learning_unit_year_subtypes.PARTIM)
        learning_unit_year_2 = LearningUnitYearFactory(academic_year=academic_year,
                                                       learning_container_year=l_container_year_2,
                                                       subtype=learning_unit_year_subtypes.FULL)
        LearningUnitYearFactory(academic_year=academic_year, learning_container_year=None)

        all_partims_container_year_1 = get_partims_related(learning_unit_year_1)
        self.assertEqual(len(all_partims_container_year_1), 2)
        all_partims_container_year_2 = get_partims_related(learning_unit_year_2)
        self.assertEqual(len(all_partims_container_year_2), 0)