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

from base.models.enums.academic_calendar_type import AcademicCalendarTypes
from base.tests.factories.academic_calendar import OpenAcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory, get_current_year
from base.tests.factories.campus import CampusFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.entity_version import MainEntityVersionFactory
from base.tests.factories.organization import MainOrganizationFactory
from base.utils.urls import reverse_with_get
from education_group.ddd.domain import mini_training
from education_group.ddd.factories.group import GroupFactory
from education_group.tests.factories.auth.central_manager import CentralManagerFactory
from education_group.tests.factories.mini_training import MiniTrainingFactory, MiniTrainingIdentityFactory
from reference.tests.factories.language import FrenchLanguageFactory


class TestMiniTrainingUpdateView(TestCase):
    @classmethod
    def setUpTestData(cls):
        FrenchLanguageFactory()
        AcademicYearFactory.produce()
        cls.mini_training_identity = MiniTrainingIdentityFactory(year=get_current_year())
        cls.mini_training = MiniTrainingFactory(
            entity_identity=cls.mini_training_identity,
            start_year=get_current_year()-1
        )
        cls.organization = MainOrganizationFactory()
        cls.teaching_campus = CampusFactory(organization=cls.organization)
        cls.url = reverse_with_get(
            "mini_training_update",
            kwargs={
                "code": cls.mini_training.code,
                "year": cls.mini_training_identity.year,
                "acronym": cls.mini_training_identity.acronym
            },
            get={"path": "1|2|3"}
        )
        cls.egy = EducationGroupYearFactory(
            partial_acronym=cls.mini_training.code,
            academic_year__year=cls.mini_training.year,
            management_entity=MainEntityVersionFactory(entity__organization=cls.organization).entity
        )
        OpenAcademicCalendarFactory(
            reference=AcademicCalendarTypes.EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT.name,
            data_year=cls.egy.academic_year
        )
        cls.central_manager = CentralManagerFactory(entity=cls.egy.management_entity)

    def setUp(self):
        self.get_mini_training_patcher = mock.patch(
            "education_group.ddd.service.read.get_mini_training_service.get_mini_training",
            return_value=self.mini_training
        )
        self.mocked_get_mini_training = self.get_mini_training_patcher.start()
        self.addCleanup(self.get_mini_training_patcher.stop)

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
        self.assertTrue("mini_training_form" in context)
        self.assertTemplateUsed(response, "education_group_app/mini_training/upsert/update.html")

    @mock.patch("education_group.views.mini_training.update.MiniTrainingUpdateView."
                "get_success_msg_updated_mini_trainings", return_value=[])
    @mock.patch("education_group.views.mini_training.update.MiniTrainingUpdateView.update_mini_training")
    def test_should_call_mini_training_and_link_services_when_forms_are_valid_without_end_year(
            self,
            update_mini_training,
            *mocks
    ):
        update_mini_training.return_value = [
            mini_training.MiniTrainingIdentity(acronym="ACRONYM", year=get_current_year()-1)
        ]
        response = self.client.post(self.url, data=self._get_form_data())

        self.assertTrue(update_mini_training.called)

        expected_redirec_url = reverse_with_get(
            'element_identification',
            kwargs={"code": self.mini_training.code, "year": self.mini_training_identity.year},
            get={"path": "1|2|3"}
        )
        self.assertRedirects(response, expected_redirec_url, fetch_redirect_response=False)\


    @mock.patch("education_group.views.mini_training.update.MiniTrainingUpdateView."
                "get_success_msg_updated_mini_trainings", return_value=[])
    @mock.patch("education_group.views.mini_training.update.MiniTrainingUpdateView.update_mini_training")
    def test_should_call_mini_training_and_link_services_when_forms_are_valid_with_end_year(
            self,
            update_mini_training,
            *mocks
    ):
        OpenAcademicCalendarFactory(
            reference=AcademicCalendarTypes.EDUCATION_GROUP_EXTENDED_DAILY_MANAGEMENT.name,
            data_year__year=self.egy.academic_year.year + 1
        )

        update_mini_training.return_value = [
            mini_training.MiniTrainingIdentity(acronym="ACRONYM", year=get_current_year()-1)
        ]

        form_data = self._get_form_data()

        # set end year
        form_data['end_year'] = get_current_year()+1

        response = self.client.post(self.url, data=form_data)

        self.assertTrue(update_mini_training.called)

        expected_redirec_url = reverse_with_get(
            'element_identification',
            kwargs={"code": self.mini_training.code, "year": self.mini_training_identity.year},
            get={"path": "1|2|3"}
        )
        self.assertRedirects(response, expected_redirec_url, fetch_redirect_response=False)

    def _get_form_data(self):
        return {
            'code': self.mini_training.code,
            'type': self.mini_training.type,
            'academic_year': get_current_year()+1,
            'abbreviated_title': self.mini_training.abbreviated_title,
            'titles': self.mini_training.titles,
            'status': self.mini_training.status.name,
            'schedule_type': self.mini_training.schedule_type.name,
            'credits': self.mini_training.credits,
            'management_entity': self.egy.management_entity.most_recent_entity_version.acronym,
            'start_year': self.mini_training.start_year,
            'end_year': self.mini_training.end_year or '',
            'title_fr': 'title_fr',
            'teaching_campus': self.teaching_campus.name,
        }
