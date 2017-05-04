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
from django.test import TestCase
from base.models.learning_container import LearningContainer
from base.models.learning_container_year import LearningContainerYear
from base.models.learning_component import LearningComponent
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_unit_year import LearningUnitYear
from base.models.learning_unit_component import LearningUnitComponent
from base.models.academic_year import AcademicYear
from base.enums import learning_unit_year_types

now = datetime.datetime.now()


class LearningComponentYearTest(TestCase):

    current_academic_year = None

    def setUp(self):
        self.current_academic_year = AcademicYear(year=(now.year),
                                     start_date=datetime.datetime(now.year, now.month, 15),
                                     end_date=datetime.datetime(now.year + 1, now.month, 28))
        self.current_academic_year.save()

        self.current_academic_year_different = AcademicYear(year=(now.year)-1,
                                     start_date=datetime.datetime(now.year-1, now.month, 15),
                                     end_date=datetime.datetime(now.year + 2, now.month, 28))
        self.current_academic_year_different.save()

    def test_creation_learning_unit_component_class_with_different_year(self):

        learning_container = LearningContainer()
        learning_component = LearningComponent(learning_container=learning_container)

        learning_container_year = LearningContainerYear(title="Biology",
                                                        acronym="LBIO1212",
                                                        academic_year=self.current_academic_year,
                                                        learning_container=learning_container)
        #Composant annualisé est associé à son composant et à son conteneur annualisé
        learning_component_year = LearningComponentYear(learning_container_year=learning_container_year,
                                                        learning_component=learning_component,
                                                        title="Cours magistral",
                                                        acronym="/C",
                                                        type=learning_unit_year_types.COURSE,
                                                        comment="TEST")

        #UE associée à un conteneur d'une année différente du composant
        learning_unit_year = LearningUnitYear(  title="Biology",
                                                acronym="LBIO1212",
                                                academic_year=self.current_academic_year_different,
                                                learning_container_year=learning_container_year)

        #Association du conteneur et de son composant dont les années académiques diffèrent l'une de l'autre
        learning_unit_component = LearningUnitComponent(learning_component_year=learning_component_year,
                                                        learning_unit_year=learning_unit_year)

        self.assertEqual(learning_component_year.learning_container_year, learning_unit_year.learning_container_year)