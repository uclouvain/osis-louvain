from typing import List

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase


class APIFilterTestCaseData:
    filters = None
    expected_result = None

    def __init__(self, filters, expected_result):
        self.filters = filters
        self.expected_result = expected_result

    def __str__(self):
        return """
            filters = {filters} \n
            expected_result = {expected_result} \n
        """.format(filters=self.filters, expected_result=self.expected_result)


def requires_attributes(attributes: List[str]):
    def attribute_required_decorator(func):
        def function_wrapper(self):
            for attr in attributes:
                if getattr(self, attr) is None:
                    raise NotImplementedError("Please set the param '{}' to run this unit test.".format(attr))
            func(self)
        return function_wrapper
    return attribute_required_decorator


def only_run_if_called_from_subclass(func):
    """Prevent test execution from Mixin class"""
    def function_wrapper(self):
        if APIDefaultTestsCasesHttpGetMixin not in self.__class__.__bases__:
            self.skipTest("Test not called from a subclass.")
        func(self)
    return function_wrapper


class APIDefaultTestsCasesHttpGetMixin(APITestCase):

    http_method = 'GET'  # Could write a mixin with "post", "put"...
    user = None
    url = None
    methods_not_allowed = None

    has_api_pagination = True
    has_api_filters = True

    def setUp(self):
        if not self.user:
            self.user = User()
        self.client.force_authenticate(user=self.user)

    @only_run_if_called_from_subclass
    @requires_attributes(['url'])
    def test_when_not_authenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @only_run_if_called_from_subclass
    @requires_attributes(['url'])
    def test_authentication(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @only_run_if_called_from_subclass
    @requires_attributes(['url', 'methods_not_allowed'])
    def test_methods_not_allowed(self):
        for method in self.methods_not_allowed:
            response = getattr(self.client, method)(self.url)
            self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    @only_run_if_called_from_subclass
    def test_pagination(self):
        response = self.client.get(self.url)
        assertions = (
            'previous' in response.data,
            'next' in response.data,
            'results' in response.data,
            'count' in response.data,
        )
        for assertion in assertions:
            if self.has_api_pagination:
                self.assertTrue(assertion)
            else:
                self.assertFalse(assertion)

    @only_run_if_called_from_subclass
    @requires_attributes(['url'])
    def test_filters(self):
        for counter, api_test_case in enumerate(self.get_filter_test_cases()):
            response = self.client.get(self.url, data=api_test_case.filters)
            result = response.data['results']
            msg = "\n \n Test case number {counter}. Data :\n {data} \n result = {result}".format(
                counter=counter,
                data=api_test_case,
                result=result
            )
            self.assertEqual(result, api_test_case.expected_result, msg=msg)

    def get_filter_test_cases(self) -> List[APIFilterTestCaseData]:
        if self.has_api_filters:
            raise NotImplementedError(
                "Please implements function {function} or set the param {param} to False "
                "if your API doesn't have any filter.".format(
                    function="get_filter_test_cases()",
                    param="has_api_filters"
                )
            )
        return []
