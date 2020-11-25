##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from unittest import mock

from django.test import TestCase, RequestFactory, SimpleTestCase
from django.views.generic import TemplateView

from base.tests.factories.user import UserFactory
from base.utils.cache import cache, RequestCache, CacheFilterMixin, cached_result


class TestRequestCache(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.path = 'dummy_url'
        cls.request_cache = RequestCache(cls.user, cls.path)
        cls.request_data = {"name": ["Axandre", "Jean"], "city": ["City25"]}

    def setUp(self):
        request_factory = RequestFactory()
        self.request = request_factory.get("www.url.com", data=self.request_data)
        self.addCleanup(cache.clear)

    def test_key(self):
        expected_key = RequestCache.PREFIX_KEY + '_' + str(self.user.id) + '_' + self.path
        actual_key = self.request_cache.key
        self.assertEqual(
            expected_key,
            actual_key
        )

    def test_save_and_restore_get_parameters(self):
        self.request_cache.save_get_parameters(self.request)
        expected_dict = dict(self.request_cache.restore_get_request(self.request).lists())
        self.assertDictEqual(
            expected_dict,
            self.request_data
        )

    def test_use_default_values(self):
        default_values = {
            "name": "A name",
            "city": "A city",
        }
        self.assertDictEqual(
            self.request_cache.restore_get_request(self.request, **default_values).dict(),
            default_values
        )

    def test_exclude_parameters(self):
        self.request_cache.save_get_parameters(self.request, parameters_to_exclude=['name'])
        expected_result = self.request_data.copy()
        del expected_result["name"]
        self.assertDictEqual(
            self.request_cache.cached_data,
            expected_result
        )


class TestCacheFilterMixin(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.path = 'dummy_url'
        cls.request_data = {"country": ["Belgium"], "city": ["Louvain-la-neuve"]}

    def setUp(self):
        request_factory = RequestFactory()
        self.request = request_factory.get("www.dummy.com", data=self.request_data)
        self.addCleanup(cache.clear)

    @mock.patch('base.utils.cache.RequestCache.restore_get_request')
    def test_assert_restore_get_request_called(self, mock_restore_get_request):
        class DummyClass(CacheFilterMixin, TemplateView):
            template_name = 'test.html'

        self.request.user = self.user
        obj = DummyClass(request=self.request)
        obj.get(self.request)
        self.assertTrue(mock_restore_get_request.called)

    @mock.patch('base.utils.cache.RequestCache.save_get_parameters')
    def test_assert_save_get_request_not_called_because_excluding_keys(self, mock_save_get_parameters):
        class DummyClass(CacheFilterMixin, TemplateView):
            template_name = 'test.html'
            cache_exclude_params = ['country', 'city']

        self.request.user = self.user
        obj = DummyClass(request=self.request)
        obj.get(self.request)
        self.assertFalse(mock_save_get_parameters.called)


class TestCachedResult(SimpleTestCase):
    @cached_result
    def _function_cached_for_test(self, number_to_increment: int):
        return number_to_increment + 1

    def test_function_cached(self):
        incremented_number = 0
        incremented_number = self._function_cached_for_test(incremented_number)  # Increment 1
        incremented_number = self._function_cached_for_test(incremented_number)  # Increment 2
        incremented_number = self._function_cached_for_test(incremented_number)  # Increment 3
        expected_result = 1
        self.assertTrue(hasattr(self, '__cached__function_cached_for_test'))
        self.assertEqual(
            incremented_number,
            expected_result,
            "Function called 3 times, but should have been executed only the first time"
        )
        self.assertNotEqual(
            incremented_number,
            3,
            "Function called 3 times, but should have been executed only the first time"
        )
