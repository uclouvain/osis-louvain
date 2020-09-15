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
import mock
from django.test import TestCase

from base.utils.urls import reverse_with_get
from education_group.ddd.domain import training, group
from education_group.ddd.factories.group import GroupFactory
from education_group.tests.ddd.factories.training import TrainingFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from reference.tests.factories.language import FrenchLanguageFactory
from testing import mocks


class TestTrainingUpdateView(TestCase):
    @classmethod
    def setUpTestData(cls):
        FrenchLanguageFactory()
        cls.central_manager = CentralManagerFactory()
        cls.url = reverse_with_get(
            "training_update",
            kwargs={"code": "CODE", "year": 2020, "title": "ACRONYM"},
            get={"path_to": "1|2|3"}
        )

    def setUp(self):
        self.client.force_login(self.central_manager.person.user)

    @mock.patch("education_group.ddd.service.read.get_training_service.get_training")
    @mock.patch("education_group.ddd.service.read.get_group_service.get_group")
    def test_should_display_forms_when_good_get_request(
            self,
            mock_get_group,
            mock_get_training):
        mock_get_training.return_value = TrainingFactory()
        mock_get_group.return_value = GroupFactory()

        response = self.client.get(self.url)

        context = response.context
        self.assertTrue("training_form" in context)
        self.assertTemplateUsed(response, "education_group_app/training/upsert/update.html")

    @mock.patch("education_group.ddd.service.read.get_update_training_warning_messages.get_conflicted_fields",
                return_value=[])
    @mock.patch("education_group.views.training.update.TrainingUpdateView.get_training_obj")
    @mock.patch("education_group.ddd.service.read.get_group_service.get_group")
    @mock.patch("education_group.views.training.update.TrainingUpdateView.update_training")
    @mock.patch("education_group.views.training.update.TrainingUpdateView.delete_training")
    @mock.patch("education_group.views.training.update.TrainingUpdateView.report_training")
    @mock.patch("education_group.views.training.update.TrainingUpdateView.training_form",
                new_callable=mocks.MockFormValid)
    def test_should_call_training_and_link_services_when_forms_are_valid(
            self,
            get_training_form_mock,
            report_training,
            delete_training,
            update_training,
            mock_get_group,
            mock_get_training,
            mock_warning_messages):
        mock_get_training.return_value = TrainingFactory()
        mock_get_group.return_value = GroupFactory()
        update_training.return_value = [training.TrainingIdentity(acronym="ACRONYM", year=2020)]
        delete_training.return_value = []
        report_training.return_value = []
        response = self.client.post(self.url, data={})

        self.assertTrue(update_training.called)
        self.assertTrue(delete_training.called)

        expected_redirec_url = reverse_with_get(
            'element_identification',
            kwargs={"code": "CODE", "year": 2020},
            get={"path": "1|2|3"}
        )
        self.assertRedirects(response, expected_redirec_url, fetch_redirect_response=False)

