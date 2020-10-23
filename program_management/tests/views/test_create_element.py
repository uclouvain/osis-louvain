import mock
from django import forms
from django.http import HttpResponseBadRequest
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import pgettext_lazy

from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import GroupType
from education_group.ddd.factories.group import GroupFactory
from program_management.forms.select_type import SelectTypeForm
from education_group.tests.factories.auth.central_manager import CentralManagerFactory


class TestSelectTypeCreateView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.central_manager = CentralManagerFactory()
        cls.url = reverse('create_element_select_type', kwargs={'category': Categories.GROUP.name})

    def setUp(self) -> None:
        self.client.force_login(self.central_manager.person.user)

    def test_case_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_case_get_method_with_invalid_category_assert_bad_request(self):
        url_with_invalid_category = reverse('create_element_select_type', kwargs={'category': 'Unknown categ'})
        response = self.client.get(url_with_invalid_category)

        self.assertEqual(response.status_code, HttpResponseBadRequest.status_code)

    def test_case_get_assert_context(self):
        response = self.client.get(self.url)

        self.assertIsInstance(response.context['form'], SelectTypeForm)

    @mock.patch('program_management.views.create_element.SelectTypeCreateElementView.get_parent_group_obj')
    @mock.patch('program_management.views.create_element.SelectTypeForm.get_name_choices', return_value=[])
    def test_case_get_assert_error_set_in_context_when_choice_contains_only_blank(
        self,
        mock_init_name_choice,
        mock_get_parent_group,
    ):
        mock_get_parent_group.return_value = GroupFactory(type=GroupType.COMMON_CORE)

        url = self.url + "?path_to=656|45454"
        response = self.client.get(url)

        expected_error_msg = pgettext_lazy(
            "male",
            "It is impossible to create a %(category)s under a parent type of %(parent_type)s"
        ) % {
            'category': str(Categories.GROUP.value).lower(),
            'parent_type': str(GroupType.COMMON_CORE.value).lower()
        }
        self.assertEqual(response.context['error'], expected_error_msg)

    def test_case_post_method_with_invalid_category_assert_bad_request(self):
        url_with_invalid_category = reverse('create_element_select_type', kwargs={'category': 'Unknown categ'})
        response = self.client.post(url_with_invalid_category)

        self.assertEqual(response.status_code, HttpResponseBadRequest.status_code)

    @mock.patch('program_management.views.create_element.SelectTypeForm.is_valid', return_value=True)
    @mock.patch('program_management.views.create_element.SelectTypeForm.cleaned_data',
                new_callable=mock.PropertyMock, create=True)
    def test_case_group_type_valid_post_assert_redirect_to_group_create(self, mock_form_cleaned_data, *args, **kwargs):
        mock_form_cleaned_data.return_value = {'name': GroupType.COMMON_CORE.name}
        response = self.client.post(self.url, data={})

        self.assertRedirects(
            response,
            reverse('group_create', kwargs={'type': GroupType.COMMON_CORE.name}),
            fetch_redirect_response=False
        )

    @mock.patch('program_management.views.create_element.SelectTypeForm.get_name_choices')
    @mock.patch('program_management.views.create_element.SelectTypeForm.is_valid', return_value=True)
    @mock.patch('program_management.views.create_element.SelectTypeForm.cleaned_data',
                new_callable=mock.PropertyMock, create=True)
    def test_case_group_type_valid_post_assert_redirect_to_group_create_with_path_queryparam(
            self,
            mock_form_cleaned_data,
            *args, **kwargs
    ):
        mock_form_cleaned_data.return_value = {'name': GroupType.COMMON_CORE.name}

        url_with_path_to_queryparam = self.url + "?path_to=656|45454|6556"
        response = self.client.post(url_with_path_to_queryparam, data={})

        expected_redirect = reverse('group_create', kwargs={'type': GroupType.COMMON_CORE.name}) + \
            "?path_to=656|45454|6556"
        self.assertRedirects(response, expected_redirect, fetch_redirect_response=False)
