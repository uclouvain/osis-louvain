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
from django.http import HttpResponse
from django.test import TestCase

from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.utils.urls import reverse_with_get
from education_group.ddd.domain import training
from education_group.ddd.domain.exception import MaximumCertificateAimType2Reached
from education_group.tests.ddd.factories.group import GroupFactory
from education_group.tests.ddd.factories.training import TrainingFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.tests.factories.auth.faculty_manager import FacultyManagerFactory
from reference.tests.factories.language import FrenchLanguageFactory
from testing import mocks


class TestTrainingUpdateView(TestCase):
    @classmethod
    def setUpTestData(cls):
        FrenchLanguageFactory()
        AcademicYearFactory.produce()
        cls.url = reverse_with_get(
            "training_update",
            kwargs={"code": "CODE", "year": 2020, "title": "ACRONYM"},
            get={"path_to": "1|2|3"}
        )
        cls.training = TrainingFactory()
        cls.egy = EducationGroupYearFactory(partial_acronym=cls.training.code, academic_year__year=cls.training.year)
        OpenAcademicCalendarFactory(
            reference=AcademicCalendarTypes.EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT.name,
            data_year=cls.egy.academic_year
        )
        cls.central_manager = CentralManagerFactory(entity=cls.egy.management_entity)

    def setUp(self):
        self.get_training_patcher = mock.patch(
            "education_group.ddd.service.read.get_training_service.get_training",
            return_value=self.training
        )
        self.mocked_get_training = self.get_training_patcher.start()
        self.addCleanup(self.get_training_patcher.stop)

        self.get_group_patcher = mock.patch(
            "education_group.ddd.service.read.get_group_service.get_group",
            return_value=GroupFactory()
        )
        self.mocked_get_group = self.get_group_patcher.start()
        self.addCleanup(self.get_group_patcher.stop)

        self.client.force_login(self.central_manager.person.user)

    def test_should_display_forms_when_good_get_request(self):
        response = self.client.get(self.url)

        context = response.context
        self.assertTrue("training_form" in context)
        self.assertTemplateUsed(response, "education_group_app/training/upsert/update.html")

    @mock.patch("education_group.views.training.update.TrainingUpdateView."
                "get_success_msg_deleted_trainings", return_value=[])
    @mock.patch("education_group.views.training.update.TrainingUpdateView.update_training")
    @mock.patch("education_group.views.training.update.TrainingUpdateView.delete_training")
    @mock.patch("education_group.views.training.update.TrainingUpdateView.training_form",
                new_callable=mocks.MockFormValid)
    def test_should_call_training_and_link_services_when_forms_are_valid(
            self,
            get_training_form_mock,
            delete_training,
            update_training,
            *mocks
    ):
        update_training.return_value = [training.TrainingIdentity(acronym="ACRONYM", year=2020)]
        delete_training.return_value = []
        response = self.client.post(self.url, data={})

        self.assertTrue(update_training.called)
        self.assertTrue(delete_training.called)

        expected_redirec_url = reverse_with_get(
            'element_identification',
            kwargs={"code": "CODE", "year": 2020},
            get={"path": "1|2|3"}
        )
        self.assertRedirects(response, expected_redirec_url, fetch_redirect_response=False)

    def test_should_disable_or_enable_certificate_aim_according_to_role(self):
        # For faculty manager, we must have an opened calendar for creation of training
        OpenAcademicCalendarFactory(
            reference=AcademicCalendarTypes.EDUCATION_GROUP_EDITION.name,
            data_year=self.egy.academic_year
        )

        rules = [
           {'role': CentralManagerFactory(entity=self.egy.management_entity), 'is_disabled': True},
           {'role': FacultyManagerFactory(entity=self.egy.management_entity), 'is_disabled': True},
           {'role': ProgramManagerFactory(education_group=self.egy.education_group), 'is_disabled': False},
        ]
        for rule in rules:
            self._test_certificate_aim_according_to_role(role=rule['role'], is_disabled=rule['is_disabled'])

    def _test_certificate_aim_according_to_role(self, role, is_disabled: bool):
        self.client.force_login(role.person.user)
        response = self.client.get(self.url)
        form = response.context['training_form']
        self.assertEqual(form.fields['certificate_aims'].disabled, is_disabled)

    @mock.patch('django.forms.forms.BaseForm.changed_data', new_callable=mock.PropertyMock)
    @mock.patch('education_group.forms.training.CreateTrainingForm.is_valid', return_value=True)
    @mock.patch('education_group.views.training.update.TrainingUpdateView.delete_training', return_value=[])
    @mock.patch('education_group.views.training.update.TrainingUpdateView.update_training')
    @mock.patch('education_group.views.training.update.TrainingUpdateView.update_certificate_aims')
    def test_should_update_certificate_aims_only_if_unique_field_changed(
            self,
            mock_update_aims,
            mock_update_training,
            mock_delete_training,
            mock_form_valid,
            mock_changed_data,
    ):
        mock_changed_data.return_value = ['certificate_aims']

        self.client.post(self.url, data={'certificate_aims': []})

        self.assertFalse(mock_update_training.called)
        self.assertTrue(mock_update_aims.called)

    @mock.patch('education_group.views.training.update.TrainingUpdateView.delete_training', return_value=[])
    @mock.patch('education_group.views.training.update.TrainingUpdateView.update_training')
    @mock.patch('education_group.views.training.update.postpone_certificate_aims_modification')
    @mock.patch("education_group.views.training.update.TrainingUpdateView.training_form",
                new_callable=mocks.MockFormValid)
    @mock.patch('education_group.views.training.update.render')
    def test_should_not_update_certificate_aims_when_maximum_of_type_2_aims_is_reached(
            self,
            mock_render,
            mock_form_valid,
            mock_postpone_certificate_aims_modification,
            mock_update_training,
            mock_delete_training,
    ):
        mock_postpone_certificate_aims_modification.side_effect = MaximumCertificateAimType2Reached
        mock_form_valid.changed_data = ['certificate_aims']
        mock_render.return_value = HttpResponse()

        self.client.post(self.url)
        self.assertTrue(mock_form_valid.errors)
