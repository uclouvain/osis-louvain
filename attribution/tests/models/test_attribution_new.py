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

from attribution.models import attribution_new
from attribution.tests.factories.attribution_new import AttributionNewFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.tutor import TutorFactory


class AttributionChargeNewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tutor = TutorFactory()
        cls.learning_container_year = LearningContainerYearFactory()
        cls.attribution_new = AttributionNewFactory(learning_container_year=cls.learning_container_year,
                                                    start_year=2018, end_year=2020, tutor=cls.tutor,
                                                    score_responsible=True)

    def test_duration(self):
        self.assertEqual(self.attribution_new.duration, 3)

    def test_duration_without_end_year(self):
        attribution_new_without_end_year = AttributionNewFactory(start_year=2018, end_year=None)
        self.assertIsNone(attribution_new_without_end_year.duration)

    def test_search_with_tutor(self):
        result = attribution_new.search(tutor=self.tutor)
        self.assertCountEqual(result, [self.attribution_new])

    def test_search_with_learning_container_year(self):
        result = attribution_new.search(learning_container_year=self.learning_container_year)
        self.assertCountEqual(result, [self.attribution_new])

    def test_search_with_learning_container_years(self):
        result = attribution_new.search(learning_container_year__in=[self.learning_container_year])
        self.assertCountEqual(result, [self.attribution_new])

    def test_search_with_score_responsible(self):
        result = attribution_new.search(score_responsible=True)
        self.assertCountEqual(result, [self.attribution_new])

    def test_search_with_global_id(self):
        result = attribution_new.search(global_id=self.tutor.person.global_id)
        self.assertCountEqual(result, [self.attribution_new])

    def test_search_with_global_ids(self):
        result = attribution_new.search(global_id__in=[self.tutor.person.global_id])
        self.assertCountEqual(result, [self.attribution_new])
