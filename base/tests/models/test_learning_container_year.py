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
from base.models import learning_container_year
from base.tests.factories.learning_container import LearningContainerFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from django.test import TestCase

class LearningContainerYearTest(TestCase):
    def test_title_learning_container_different_from_title_learning_container_year(self):
        l_container = LearningContainerFactory(title="LC-98998")
        l_container_year = LearningContainerYearFactory.build(title="LC-DIFFERENT", learning_container=l_container)
        with self.assertRaises(AttributeError):
            l_container_year.save()

    def test_find_by_id_with_id(self):
        l_container_year = LearningContainerYearFactory()
        self.assertEqual(l_container_year, learning_container_year.find_by_id(l_container_year.id))

    def test_find_by_id_with_wrong_value(self):
        with self.assertRaises(ValueError):
            learning_container_year.find_by_id("BAD VALUE")