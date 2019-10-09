# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.urls import reverse

from base.models.education_group_year import EducationGroupYear
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.user import SuperUserFactory


class TestQuickSearchView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.luy_to_find = LearningUnitYearFactory(acronym='CYN', specific_title='Drop dead cynical')
        cls.egy_to_find = EducationGroupYearFactory(acronym='RAV', title='The Ravenlord')
        cls.user = SuperUserFactory()
        cls.next_academic_year = AcademicYearFactory(year=cls.luy_to_find.academic_year.year + 1)

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_learning_unit_search_text_filter(self):
        response = self.client.get(reverse('quick_search_learning_unit'), data={'search_text': 'dead'})
        self.assertTemplateUsed(response, 'base/quick_search_inner.html')
        self.assertIn(self.luy_to_find, response.context['object_list'])

        response = self.client.get(reverse('quick_search_learning_unit'), data={'search_text': 'asgard'})
        self.assertNotIn(self.luy_to_find, response.context['object_list'])

        self.assertEqual(self.client.session.get('quick_search_model'), LearningUnitYear.__name__)

    def test_learning_unit_academic_year_filter(self):
        response = self.client.get(reverse('quick_search_learning_unit'),
                                   data={'academic_year': self.luy_to_find.academic_year.pk})
        self.assertIn(self.luy_to_find, response.context['object_list'])

        response = self.client.get(reverse('quick_search_learning_unit'),
                                   data={'academic_year': self.next_academic_year.pk})
        self.assertNotIn(self.luy_to_find, response.context['object_list'])

    def test_education_group_search_text_filter(self):
        response = self.client.get(reverse('quick_search_education_group'), data={'search_text': 'Rav'})
        self.assertTemplateUsed(response, 'base/quick_search_inner.html')
        self.assertIn(self.egy_to_find, response.context['object_list'])

        response = self.client.get(reverse('quick_search_education_group'), data={'search_text': 'Yggdrasil'})
        self.assertNotIn(self.egy_to_find, response.context['object_list'])

        self.assertEqual(self.client.session.get('quick_search_model'), EducationGroupYear.__name__)

    def test_search_wrong_page(self):
        response = self.client.get(reverse('quick_search_learning_unit'), data={'search_text': 'dead', 'page': 2})
        self.assertIn(self.luy_to_find, response.context['object_list'])
        self.assertEqual(response.context['page_obj'].number, 1)
