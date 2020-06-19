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

from base.tests.factories.education_group_year import GroupFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.user import SuperUserFactory
from base.utils.urls import reverse_with_get
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.tests.factories.element import ElementGroupYearFactory


class TestQuickSearchLearningUnitYearView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root_element = ElementGroupYearFactory()
        cls.luy_to_find = LearningUnitYearFactory(acronym='CYN', specific_title='Drop dead cynical')
        cls.user = SuperUserFactory()
        cls.path = str(cls.root_element.id)
        cls.url = reverse_with_get(
            'quick_search_learning_unit',
            args=[cls.root_element.group_year.academic_year.year]
        )

    def setUp(self) -> None:
        self.client.force_login(self.user)

        self.addCleanup(cache.clear)

    def test_show_no_data_when_no_criteria_set(self):
        response = self.client.get(self.url, data={'path': self.path})
        self.assertTemplateUsed(response, 'quick_search_luy_inner.html')
        self.assertFalse(list(response.context['page_obj']))

    def test_learning_unit_search_filter(self):
        response = self.client.get(self.url, data={'title': 'dead', 'path': self.path})
        self.assertTemplateUsed(response, 'quick_search_luy_inner.html')
        self.assertIn(self.luy_to_find, response.context['page_obj'])

        response = self.client.get(self.url, data={'title': 'asgard', 'path': self.path})
        self.assertNotIn(self.luy_to_find, response.context['page_obj'])

    def test_return_json_when_accept_header_set_to_json(self):
        response = self.client.get(self.url, data={'title': 'dead', 'path': self.path}, HTTP_ACCEPT="application/json")

        self.assertIsInstance(response, JsonResponse)


class TestQuickSearchGroupYearView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root_element = ElementGroupYearFactory()
        cls.group_to_find = GroupYearFactory(acronym='RAV', title_fr='The Ravenlord', partial_acronym="RV")
        cls.user = SuperUserFactory()
        cls.path = str(cls.root_element.id)
        cls.url = reverse_with_get(
            'quick_search_education_group',
            args=[cls.root_element.group_year.academic_year.year],
        )

    def setUp(self) -> None:
        self.client.force_login(self.user)

        self.addCleanup(cache.clear)

    def test_show_no_data_when_no_criteria_set(self):
        response = self.client.get(self.url, data={'path': self.path})
        self.assertTemplateUsed(response, 'quick_search_egy_inner.html')
        self.assertFalse(list(response.context['page_obj']))

    def test_education_group_search_filter(self):
        response = self.client.get(self.url, data={'title': 'Rav', 'path': self.path})
        self.assertTemplateUsed(response, 'quick_search_egy_inner.html')
        self.assertIn(self.group_to_find, response.context['page_obj'])

        response = self.client.get(self.url, data={'title': 'Yggdrasil', 'path': self.path})
        self.assertNotIn(self.group_to_find, response.context['page_obj'])

    def test_return_json_when_accept_header_set_to_json(self):
        response = self.client.get(self.url, data={'title': 'dead', 'path': self.path}, HTTP_ACCEPT="application/json")

        self.assertIsInstance(response, JsonResponse)
