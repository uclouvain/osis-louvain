##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from datetime import date
from unittest import mock

from django.test import TestCase
from django.test.utils import override_settings

from attribution.business import application_json
from attribution.tests.factories.tutor_application import TutorApplicationFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.tutor import TutorFactory


class AttributionJsonTest(TestCase):
    def setUp(self):
        today = date.today()
        self.academic_year = AcademicYearFactory(year=today.year, start_date=today)
        self.l_container_1 = LearningContainerYearFactory(in_charge=True)
        self.tutor_1 = TutorFactory(person=PersonFactory(global_id='00012345'))
        self.tutor_2 = TutorFactory(person=PersonFactory(global_id=''))
        self.tutor_3 = TutorFactory(person=PersonFactory(global_id=None))
        self.tutor_application_1 = TutorApplicationFactory(tutor=self.tutor_1,
                                                           learning_container_year=self.l_container_1)
        self.tutor_application_2 = TutorApplicationFactory(tutor=self.tutor_2,
                                                           learning_container_year=self.l_container_1)
        self.tutor_application_3 = TutorApplicationFactory(tutor=self.tutor_3,
                                                           learning_container_year=self.l_container_1)

    @mock.patch('osis_common.queue.queue_sender.send_message')
    @override_settings(QUEUES={'QUEUES_NAME':{'APPLICATION_OSIS_PORTAL': 'dummy'}})
    def test_build_attributions_json(self, mock_send_message):
        application_list = application_json._compute_list()
        self.assertIsInstance(application_list, list)
        self.assertEqual(len(application_list), 1)
        application_json.publish_to_portal()
        self.assertTrue(mock_send_message.called)

    def test_build_attributions_json_with_none_value(self):
        self.tutor_application_1.volume_lecturing = None  # Should be computed as '0.0'
        self.tutor_application_1.save()
        application_list = application_json._compute_list(global_ids=[self.tutor_1.person.global_id])
        self.assertIsInstance(application_list, list)
        self.assertEqual(len(application_list), 1)
        self.assertEqual(application_list[0]['global_id'], self.tutor_1.person.global_id)
        # We should have two applications
        self.assertIsInstance(application_list[0]['tutor_applications'], list)
        self.assertEqual(len(application_list[0]['tutor_applications']), 1)
        self.assertEqual(application_list[0]['tutor_applications'][0]['charge_lecturing_asked'], '0.0')

    def test_get_all_tutor_application_without_global_ids_empty(self):
        all_tutor_applications = application_json._get_all_tutor_application(global_ids=None)
        self.assertEqual(len(all_tutor_applications), 1)

    def test_get_all_tutor_application_with_global_ids_list(self):
        tutor_applications = application_json._get_all_tutor_application(global_ids=['00012345'])
        self.assertEqual(len(tutor_applications), 1)

    def test_group_tutor_application_by_global_id(self):
        all_tutor_applications = application_json._get_all_tutor_application(global_ids=None)
        self.assertEqual(len(all_tutor_applications), 1)
        tutor_applications_grouped = application_json._group_tutor_application_by_global_id(all_tutor_applications)
        self.assertEqual(len(tutor_applications_grouped["00012345"]["tutor_applications"]), 1)
