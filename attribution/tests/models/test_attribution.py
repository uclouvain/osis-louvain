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
import datetime

from django.test import TestCase

from attribution.models import attribution
from base.tests.factories import tutor, user, structure, entity_manager, academic_year, learning_unit_year
from base.tests.models.test_person import create_person_with_user


def create_attribution(tutor, learning_unit_year, score_responsible=False, summary_responsible=False):
    an_attribution = attribution.Attribution(tutor=tutor,
                                             learning_unit_year=learning_unit_year,
                                             score_responsible=score_responsible,
                                             summary_responsible=summary_responsible)
    an_attribution.save()
    return an_attribution


class AttributionTest(TestCase):
    def setUp(self):
        self.user = user.UserFactory()
        self.user.save()
        self.person = create_person_with_user(self.user)
        self.structure = structure.StructureFactory()
        self.structure_children = structure.StructureFactory(part_of=self.structure)
        self.entity_manager = entity_manager.EntityManagerFactory(person=self.person, structure=self.structure)
        self.tutor = tutor.TutorFactory(person=self.person)
        self.academic_year = academic_year.AcademicYearFactory(year=datetime.date.today().year,
                                                               start_date=datetime.date.today())
        self.learning_unit_year = learning_unit_year.LearningUnitYearFactory(structure=self.structure,
                                                                             acronym="LBIR1210",
                                                                             academic_year=self.academic_year)
        self.learning_unit_year_children = learning_unit_year.LearningUnitYearFactory(structure=self.structure_children,
                                                                                      acronym="LBIR1211",
                                                                                      academic_year=self.academic_year)
        self.learning_unit_year_without_attribution = learning_unit_year.LearningUnitYearFactory(structure=self.structure,
                                                                                                 acronym="LBIR1212",
                                                                                                 academic_year=self.academic_year)
        self.attribution = create_attribution(tutor=self.tutor,
                                              learning_unit_year=self.learning_unit_year,
                                              score_responsible=True,
                                              summary_responsible=True)
        self.attribution_children = create_attribution(tutor=self.tutor,
                                                       learning_unit_year=self.learning_unit_year_children,
                                                       score_responsible=False)

    def test_search(self):
        attributions = attribution.search(tutor=self.tutor,
                                          learning_unit_year=self.learning_unit_year,
                                          score_responsible=True,
                                          list_learning_unit_year=None)
        self.assertEqual(attributions[0].tutor, self.tutor)

    def test_find_responsible(self):
        responsible = attribution.find_responsible(self.learning_unit_year)
        self.assertEqual(responsible.person.first_name, self.tutor.person.first_name)

    def test_find_responsible_without_attribution(self):
        self.assertIsNone(attribution.find_responsible(self.learning_unit_year_without_attribution))

    def test_find_responsible_without_responsible(self):
        self.assertIsNone(attribution.find_responsible(self.learning_unit_year_without_attribution))

    def test_is_score_responsible(self):
        self.assertTrue(attribution.is_score_responsible(self.user, self.learning_unit_year))

    def test_is_score_responsible_without_attribution(self):
        self.assertFalse(attribution.is_score_responsible(self.user, self.learning_unit_year_without_attribution))
