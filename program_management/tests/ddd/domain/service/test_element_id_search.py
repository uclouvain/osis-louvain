# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from django.test import TestCase

from education_group.ddd.domain import mini_training
from program_management.ddd.domain.service import element_id_search
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory


class TestElementIdSearchFromMiniTrainingIdentity(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.element = ElementGroupYearFactory()
        cls.version = StandardEducationGroupVersionFactory(
            root_group=cls.element.group_year
        )

    def test_should_return_none_when_no_matching_element(self):
        mini_training_identity = mini_training.MiniTrainingIdentity(acronym='DO NOT EXIST', year=1854)

        result = element_id_search.ElementIdSearch().get_from_mini_training_identity(mini_training_identity)

        self.assertIsNone(result)

    def test_should_return_corresponding_element_id_when_matching_element(self):
        mini_training_identity = mini_training.MiniTrainingIdentity(
            acronym=self.version.offer.acronym,
            year=self.version.offer.academic_year.year
        )

        result = element_id_search.ElementIdSearch().get_from_mini_training_identity(mini_training_identity)

        self.assertEqual(
            self.element.id,
            result
        )
