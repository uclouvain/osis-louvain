from collections import defaultdict
from typing import List
from unittest import mock

from django.http import HttpResponseForbidden, HttpResponse
from django.test import TestCase
from django.urls import reverse, exceptions
from django.utils.translation import gettext_lazy as _

from base.tests.factories.education_group_type import GroupEducationGroupTypeFactory
from base.tests.factories.person import PersonFactory
from education_group.ddd.domain.exception import GroupCodeAlreadyExistException, ContentConstraintTypeMissing
from education_group.ddd.domain.group import GroupIdentity
from education_group.forms.group import GroupForm, GroupAttachForm
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from program_management.tests.factories.element import ElementGroupYearFactory
from testing import mocks


class TestCreateOrphanGroupGetMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.type = GroupEducationGroupTypeFactory()

        cls.central_manager = CentralManagerFactory()
        cls.url = reverse('group_create', kwargs={'type': cls.type.name})

    def setUp(self) -> None:
        self.client.force_login(self.central_manager.person.user)

    def test_case_when_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_when_user_has_no_permission(self):
        a_person_without_permission = PersonFactory()
        self.client.force_login(a_person_without_permission.user)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_when_type_in_url_is_not_supported(self):
        with self.assertRaises(exceptions.NoReverseMatch):
            reverse('group_create', kwargs={'type': 'dummy-type'})

    def test_assert_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "education_group_app/group/upsert/create.html")

    def test_assert_context(self):
        response = self.client.get(self.url)

        self.assertIsInstance(response.context['group_form'], GroupForm)
        self.assertIsInstance(response.context['tabs'], List)
        self.assertIsInstance(response.context['cancel_url'], str)

    def test_assert_contains_only_identification_tabs(self):
        response = self.client.get(self.url)

        self.assertListEqual(
            response.context['tabs'],
            [{
                "text": _("Identification"),
                "active": True,
                "display": True,
                "include_html": "education_group_app/group/upsert/identification_form.html"
            }]
        )

    def test_assert_cancel_url_computed(self):
        response = self.client.get(self.url)

        expected_url = reverse('version_program')
        self.assertEqual(response.context['cancel_url'], expected_url)


class TestCreateOrphanGroupPostMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.type = GroupEducationGroupTypeFactory()
        cls.central_manager = CentralManagerFactory()
        cls.url = reverse('group_create', kwargs={'type': cls.type.name})

    def setUp(self) -> None:
        self.client.force_login(self.central_manager.person.user)

    def test_case_when_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url, data={})
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_when_user_has_no_permission(self):
        a_person_without_permission = PersonFactory()
        self.client.force_login(a_person_without_permission.user)

        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_post_missing_data_assert_template_and_context(self):
        with mock.patch('education_group.views.group.create.GroupForm.is_valid', return_value=False):
            response = self.client.post(self.url, data={})
            self.assertEqual(response.status_code, HttpResponse.status_code)
            self.assertTemplateUsed(response, "education_group_app/group/upsert/create.html")

            self.assertIsInstance(response.context['group_form'], GroupForm)
            self.assertIsInstance(response.context['tabs'], List)

    @mock.patch('education_group.views.group.create.GroupForm.is_valid', return_value=True)
    @mock.patch('education_group.views.group.create.GroupForm.cleaned_data',
                new_callable=mock.PropertyMock, create=True)
    @mock.patch('education_group.views.group.create.create_group_service.create_orphan_group')
    def test_post_assert_create_service_called(self,
                                               mock_service_create_group,
                                               mock_form_clean_data,
                                               mock_form_is_valid):
        mock_service_create_group.return_value = GroupIdentity(code="LTRONC1000", year=2018)
        mock_form_clean_data.return_value = defaultdict(lambda: None)
        mock_form_is_valid.return_value = True

        self.client.post(self.url)
        self.assertTrue(mock_service_create_group.called)

    @mock.patch('education_group.views.group.create.GroupForm.is_valid', return_value=True)
    @mock.patch('education_group.views.group.create.GroupForm.cleaned_data',
                new_callable=mock.PropertyMock, create=True)
    @mock.patch('education_group.views.group.create.create_group_service.create_orphan_group')
    def test_post_assert_form_error_when_create_service_raise_exception_code_already_exist(self,
                                                                                           mock_service_create_group,
                                                                                           mock_form_clean_data,
                                                                                           mock_form_is_valid):
        mock_form_is_valid.return_value = True
        mock_form_clean_data.return_value = defaultdict(lambda: None)

        mock_service_create_group.side_effect = GroupCodeAlreadyExistException

        response = self.client.post(self.url)
        self.assertIsInstance(response.context['group_form'], GroupForm)
        self.assertTrue(response.context['group_form'].has_error('code'))

    @mock.patch('education_group.views.group.create.GroupForm.is_valid', return_value=True)
    @mock.patch('education_group.views.group.create.GroupForm.cleaned_data',
                new_callable=mock.PropertyMock, create=True)
    @mock.patch('education_group.views.group.create.create_group_service.create_orphan_group')
    def test_post_assert_form_error_when_create_service_raise_constraint_exception(self,
                                                                                   mock_service_create_group,
                                                                                   mock_form_clean_data,
                                                                                   mock_form_is_valid):
        mock_form_is_valid.return_value = True
        mock_form_clean_data.return_value = defaultdict(lambda: None)

        mock_service_create_group.side_effect = ContentConstraintTypeMissing

        response = self.client.post(self.url)
        self.assertIsInstance(response.context['group_form'], GroupForm)
        self.assertTrue(response.context['group_form'].has_error('constraint_type'))


class TestCreateNonOrphanGroupGetMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.type = GroupEducationGroupTypeFactory()

        cls.central_manager = CentralManagerFactory()
        cls.parent_element = ElementGroupYearFactory(
            group_year__management_entity=cls.central_manager.entity
        )
        cls.url = reverse('group_create', kwargs={'type': cls.type.name}) +\
            "?path_to={}".format(str(cls.parent_element.pk))

    def setUp(self) -> None:
        self.client.force_login(self.central_manager.person.user)

    def test_assert_form_instance(self):
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['group_form'], GroupAttachForm)

    def test_assert_cancel_url_computed(self):
        response = self.client.get(self.url)

        expected_url = reverse(
            'element_identification',
            kwargs={
                'code': self.parent_element.group_year.partial_acronym,
                'year': self.parent_element.group_year.academic_year.year
            }
        ) + "?path={}".format(str(self.parent_element.pk))
        self.assertEqual(response.context['cancel_url'], expected_url)


class TestCreateNonOrphanGroupPostMethod(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.type = GroupEducationGroupTypeFactory()
        cls.central_manager = CentralManagerFactory()

        cls.parent_element = ElementGroupYearFactory(
            group_year__management_entity=cls.central_manager.entity
        )
        cls.url = reverse('group_create', kwargs={'type': cls.type.name}) +\
            "?path_to={}".format(str(cls.parent_element.pk))

    def setUp(self) -> None:
        self.client.force_login(self.central_manager.person.user)

    @mock.patch('education_group.views.group.create.GroupForm.is_valid', return_value=True)
    @mock.patch('education_group.views.group.create.GroupForm.cleaned_data',
                new_callable=mock.PropertyMock, create=True)
    @mock.patch('education_group.views.group.create.create_group_and_attach_service.create_group_and_attach')
    def test_post_assert_create_service_paste_service_called(self,
                                                             mock_service_create_group,
                                                             mock_form_clean_data,
                                                             mock_form_is_valid):
        mock_service_create_group.return_value = GroupIdentity(code="LTRONC1000", year=2018)
        mock_form_clean_data.return_value = defaultdict(lambda: None)
        mock_form_is_valid.return_value = True

        self.client.post(self.url)
        self.assertTrue(mock_service_create_group.called)

    @mock.patch('education_group.views.group.create.GroupAttachForm', new_callable=mocks.MockFormValid)
    @mock.patch('education_group.views.group.create.create_group_and_attach_service.create_group_and_attach')
    def test_post_assert_redirection_with_path_queryparam(self,
                                                          mock_service_create_group,
                                                          mock_form,
                                                          *args):

        mock_service_create_group.return_value = GroupIdentity(code="LTRONC1000", year=2018)

        response = self.client.post(self.url)

        expected_redirect = \
            reverse('group_identification', kwargs={'code': 'LTRONC1000', 'year': 2018}) + \
            "?path={}".format(str(self.parent_element.pk))
        self.assertRedirects(response, expected_redirect, fetch_redirect_response=False)
