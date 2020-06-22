from unittest import mock

from django.contrib import messages
from django.http import HttpResponseRedirect
from django.test import TestCase
from django.urls import reverse

from base.business.education_groups.general_information import PublishException
from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import TrainingType

from base.tests.factories.person import PersonWithPermissionsFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory


class GeneralInformationPublishViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.training = EducationGroupVersionFactory(
            offer__acronym="APPBIOL",
            offer__academic_year__year=2019,
            offer__education_group_type__name=TrainingType.BACHELOR.name,
            offer__education_group_type__category=Categories.TRAINING.name,
            root_group__partial_acronym="LBIOL100P",
            root_group__academic_year__year=2019,
            root_group__education_group_type__name=TrainingType.BACHELOR.name,
            root_group__education_group_type__category=Categories.TRAINING.name,
        )
        cls.url = reverse('publish_general_information', kwargs={'code': 'LBIOL100P', 'year': 2019})
        cls.person = PersonWithPermissionsFactory('view_educationgroup')

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_publish_case_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_public_case_methods_not_allowed(self):
        methods_not_allowed = ['get', 'delete', 'put']
        for method in methods_not_allowed:
            request_to_call = getattr(self.client, method)
            response = request_to_call(self.url)
            self.assertEqual(response.status_code, 405)

    @mock.patch("base.business.education_groups.general_information.publish", side_effect=lambda e: "portal-url")
    def test_publish_case_ok_redirection_with_success_message(self, mock_publish):
        response = self.client.post(self.url)

        msg = [m.message for m in messages.get_messages(response.wsgi_request)]
        msg_level = [m.level for m in messages.get_messages(response.wsgi_request)]

        self.assertEqual(len(msg), 1)
        self.assertIn(messages.SUCCESS, msg_level)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    @mock.patch("base.business.education_groups.general_information.publish", side_effect=PublishException('error'))
    def test_publish_case_ko_redirection_with_error_message(self, mock_publish):
        response = self.client.post(self.url)

        msg = [m.message for m in messages.get_messages(response.wsgi_request)]
        msg_level = [m.level for m in messages.get_messages(response.wsgi_request)]

        self.assertEqual(len(msg), 1)
        self.assertIn(messages.ERROR, msg_level)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)
