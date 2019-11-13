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

from base.models import learning_container
from base.models.learning_container_year import LearningContainerYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_container import LearningContainerFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory


class LearningContainerTest(TestCase):
    def test_find_by_id_with_id(self):
        l_container = LearningContainerFactory()
        self.assertEqual(l_container, learning_container.find_by_id(l_container.id))

    def test_find_by_id_bad_value(self):
        with self.assertRaises(ValueError):
            learning_container.find_by_id("BAD VALUE")

    def test_most_recent_acronym(self):
        container = LearningContainerFactory()
        most_recent_year = 2018
        for year in range(2016, most_recent_year + 1):
            LearningContainerYearFactory(learning_container=container, academic_year=AcademicYearFactory(year=year))
        most_recent_container_year = LearningContainerYear.objects.get(academic_year__year=most_recent_year,
                                                                       learning_container=container)
        self.assertEqual(container.most_recent_acronym, most_recent_container_year.acronym)
