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
import collections
from typing import List

import mock
from django.http import HttpResponse, HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse, exceptions

from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.person import PersonFactory
from education_group.ddd.domain.training import TrainingIdentity
from education_group.forms.training import CreateTrainingForm
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.views.proxy.read import Tab
from reference.tests.factories.language import FrenchLanguageFactory


class TestTrainingCreateView(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.central_manager = CentralManagerFactory()
        cls.training_type = EducationGroupTypeFactory()
        FrenchLanguageFactory()
        cls.url = reverse('training_create', kwargs={"type": cls.training_type.name})

    def setUp(self):
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
            reverse('training_create', kwargs={'type': 'dummy-type'})

    def test_assert_context(self):
        response = self.client.get(self.url)
        self.assertIsInstance(response.context['training_form'], CreateTrainingForm)
        self.assertIsInstance(response.context['tabs'], List)
        self.assertIsInstance(response.context['type_text'], str)

    def test_should_render_template_with_correct_context_when_get_request_on_view(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed("education_group_app/training/upsert/create.html")

        context = response.context
        self.assertIsInstance(context["training_form"], CreateTrainingForm)
        self.assertEqual(context["type_text"], str(self.training_type))

    @mock.patch("education_group.views.training.create.create_and_report_training_with_program_tree")
    @mock.patch("education_group.views.training.create.CreateTrainingForm")
    def test_should_call_create_orphan_service_when_valid_post_request(self, mock_form, mock_service):
        training_id = TrainingIdentity(acronym="Acronym", year=2020)
        mock_form.return_value = self._get_form_valid_mock()
        mock_service.return_value = [training_id]
        response = self.client.post(self.url, data={})

        self.assertTrue(mock_service.called)

        expected_reverse_url = reverse('education_group_read_proxy',
            kwargs={'acronym': training_id.acronym, 'year': training_id.year}
        ) + '?tab={}'.format(Tab.IDENTIFICATION)
        self.assertRedirects(response, expected_reverse_url, fetch_redirect_response=False)

    def _get_form_valid_mock(self):
        cleaned_data = collections.defaultdict(lambda: None)
        cleaned_data["academic_year"] = mock.Mock(year=2020)
        cleaned_data["main_domain"] = mock.Mock(code='MAIN')
        cleaned_data["secondary_domains"] = []
        cleaned_data["teaching_campus"] = mock.Mock(name='Campus')
        cleaned_data["enrollment_campus"] = mock.Mock(name='Campus')
        return mock.MagicMock(is_valid=lambda: True, cleaned_data=cleaned_data, errors=list())





