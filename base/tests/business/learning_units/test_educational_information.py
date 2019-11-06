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

from attribution.tests.factories.attribution import AttributionFactory
from base.business.learning_units.educational_information import PERSON, LEARNING_UNIT_YEARS, \
    _update_responsible_data_with_new_learning_unit_yr
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.tutor import TutorFactory


class TestEducationalInformation(TestCase):

    def setUp(self):
        self.learning_unit_year_1 = LearningUnitYearFakerFactory()
        self.person_lu_1 = PersonFactory()
        self.tutor_lu1_1 = TutorFactory(person=self.person_lu_1)
        self.attribution_lu1 = AttributionFactory(learning_unit_year=self.learning_unit_year_1, tutor=self.tutor_lu1_1)
        self.learning_unit_year_1.summary_status = False
        self.learning_unit_year_1.summary_responsibles = [self.attribution_lu1]

        self.learning_unit_year_2 = LearningUnitYearFakerFactory()
        self.person_lu_2 = PersonFactory()
        self.tutor_lu1_2_1 = TutorFactory(person=self.person_lu_2)
        self.person_lu_3 = PersonFactory()
        self.tutor_lu2_2_2 = TutorFactory(person=self.person_lu_3)
        self.attribution_lu2_1 = AttributionFactory(learning_unit_year=self.learning_unit_year_2,
                                                    tutor=self.tutor_lu1_2_1)
        self.attribution_lu2_2 = AttributionFactory(learning_unit_year=self.learning_unit_year_2,
                                                    tutor=self.tutor_lu2_2_2)
        self.learning_unit_year_2.summary_status = False
        self.learning_unit_year_2.summary_responsibles = [self.attribution_lu2_1, self.attribution_lu2_2]

        self.learning_unit_year_3 = LearningUnitYearFakerFactory()
        self.attribution_lu3 = AttributionFactory(learning_unit_year=self.learning_unit_year_3, tutor=self.tutor_lu1_1)
        self.learning_unit_year_3.summary_status = False
        self.learning_unit_year_3.summary_responsibles = [self.attribution_lu3]

    def test_update_responsible_data_with_new_learning_unit_yr(self):
        list_before_update = [{PERSON: self.person_lu_2,
                               LEARNING_UNIT_YEARS: []}]
        self.assertEqual(_update_responsible_data_with_new_learning_unit_yr(self.person_lu_1,
                                                                            self.learning_unit_year_2,
                                                                            list_before_update), list_before_update)
