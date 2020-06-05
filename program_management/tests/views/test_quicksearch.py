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
from django.core.cache import cache
from django.http import JsonResponse
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.education_group_year import EducationGroupYearFactory, GroupFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.user import SuperUserFactory


class TestQuickSearchLearningUnitView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root_egy = EducationGroupYearFactory()
        cls.luy_to_find = LearningUnitYearFactory(acronym='CYN', specific_title='Drop dead cynical')
        cls.user = SuperUserFactory()
        path = str(cls.root_egy.id)
        cls.url = reverse('quick_search_learning_unit', args=[cls.root_egy.id, path])

    def setUp(self) -> None:
        self.client.force_login(self.user)

        self.addCleanup(cache.clear)

    def test_show_no_data_when_no_criteria_set(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'quick_search_luy_inner.html')
        self.assertFalse(list(response.context['page_obj']))

    def test_learning_unit_search_filter(self):
        response = self.client.get(self.url, data={'title': 'dead'})
        self.assertTemplateUsed(response, 'quick_search_luy_inner.html')
        self.assertIn(self.luy_to_find, response.context['page_obj'])

        response = self.client.get(self.url, data={'title': 'asgard'})
        self.assertNotIn(self.luy_to_find, response.context['page_obj'])

    def test_return_json_when_accept_header_set_to_json(self):
        response = self.client.get(self.url, data={'title': 'dead'}, HTTP_ACCEPT="application/json")

        self.assertIsInstance(response, JsonResponse)


class TestQuickSearchEducationGroupView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root_egy = EducationGroupYearFactory()
        cls.egy_to_find = GroupFactory(acronym='RAV', title='The Ravenlord', partial_acronym="RV")
        cls.user = SuperUserFactory()
        path = str(cls.root_egy.id)
        cls.url = reverse('quick_search_education_group', args=[cls.root_egy.id, path])

    def setUp(self) -> None:
        self.client.force_login(self.user)

        self.addCleanup(cache.clear)

    def test_show_no_data_when_no_criteria_set(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, 'quick_search_egy_inner.html')
        self.assertFalse(list(response.context['page_obj']))

    def test_education_group_search_filter(self):
        response = self.client.get(self.url, data={'title': 'Rav'})
        self.assertTemplateUsed(response, 'quick_search_egy_inner.html')
        self.assertIn(self.egy_to_find, response.context['page_obj'])

        response = self.client.get(self.url, data={'title': 'Yggdrasil'})
        self.assertNotIn(self.egy_to_find, response.context['page_obj'])

        response = self.client.get(self.url, data={'partial_acronym': 'RV'})
        self.assertIn(self.egy_to_find, response.context['page_obj'])

        response = self.client.get(self.url, data={'partial_acronym': 'RB'})
        self.assertNotIn(self.egy_to_find, response.context['page_obj'])

    def test_return_json_when_accept_header_set_to_json(self):
        response = self.client.get(self.url, data={'title': 'dead'}, HTTP_ACCEPT="application/json")

        self.assertIsInstance(response, JsonResponse)
