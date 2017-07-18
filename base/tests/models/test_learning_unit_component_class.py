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
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_class_year import LearningClassYearFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_component import LearningUnitComponentFactory
from base.tests.factories.learning_unit_component_class import LearningUnitComponentClassFactory
from base import models as mdl
from base.tests.factories.learning_unit_year import LearningUnitYearFactory


class LearningunitComponentClassTest(TestCase):

    def setUp(self):
        self.academic_year = AcademicYearFactory(year=2016)
        self.learning_unit_years = [LearningUnitYearFactory(academic_year=self.academic_year) for x in range(2)]
        self.learning_container_years = [LearningContainerYearFactory(academic_year=self.academic_year) for x in range(2)]
        self.learning_component_years = [LearningComponentYearFactory(learning_container_year=self.learning_container_years[x]) for x in range(2)]
        self.learning_unit_components = [LearningUnitComponentFactory(learning_unit_year=self.learning_unit_years[x],
                                                                      learning_component_year=self.learning_component_years[x]) for x in range(2)]
        self.learning_class_years = [LearningClassYearFactory(learning_component_year=self.learning_component_years[x]) for x in range(2)]

    def test_save_with_different_learning_component_year(self):
        with self.assertRaisesMessage(AttributeError, "Learning Component Year is different in Learning Unit Component and Learning Class Year"):
            learning_unit_component_class = LearningUnitComponentClassFactory\
                .build(learning_unit_component=self.learning_unit_components[0],
                       learning_class_year=self.learning_class_years[1])
            learning_unit_component_class.save()

    def test_find_by_learning_class_year(self):
        learning_unit_component_class = LearningUnitComponentClassFactory\
            .build(learning_unit_component=self.learning_unit_components[0],
                   learning_class_year=self.learning_class_years[0])
        learning_unit_component_class.save()
        self.assertEqual(mdl.learning_unit_component_class.find_by_learning_class_year(self.learning_class_years[0])[0],
                         learning_unit_component_class)
