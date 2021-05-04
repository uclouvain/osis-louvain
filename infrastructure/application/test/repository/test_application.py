##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
import uuid

from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from attribution.tests.factories.tutor_application import TutorApplicationFactory
from ddd.logic.application.domain.model.applicant import ApplicantIdentity
from ddd.logic.application.domain.model.application import ApplicationIdentity, Application
from infrastructure.application.repository.application import ApplicationRepository


class ApplicationRepositoryGet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tutor_application_db = TutorApplicationFactory()
        cls.repository = ApplicationRepository()

    def test_get_assert_return_not_found(self):
        application_id_unknown = ApplicationIdentity(uuid=uuid.uuid4())
        with self.assertRaises(ObjectDoesNotExist):
            self.repository.get(application_id_unknown)

    def test_get_assert_return_instance(self):
        application_id = ApplicationIdentity(uuid=self.tutor_application_db.uuid)
        application = self.repository.get(application_id)

        self.assertIsInstance(application, Application)


class ApplicationRepositorySearch(TestCase):
    @classmethod
    def setUpTestData(cls):
        global_id = "7849898989"

        cls.applicant_id = ApplicantIdentity(global_id=global_id)
        cls.tutor_application_dbs = [
            TutorApplicationFactory(tutor__person__global_id=global_id),
            TutorApplicationFactory(tutor__person__global_id=global_id),
            TutorApplicationFactory(),
        ]
        cls.repository = ApplicationRepository()

    def test_search_assert_return_no_results(self):
        entity_ids = [
            ApplicationIdentity(uuid=uuid.uuid4()),
            ApplicationIdentity(uuid=uuid.uuid4())
        ]

        self.assertListEqual(
            self.repository.search(entity_ids=entity_ids),
            []
        )

    def test_search_assert_return_filtered_by_entity_ids(self):
        tutor_application_db = TutorApplicationFactory()

        entity_ids = [
            ApplicationIdentity(uuid=tutor_application_db.uuid)
        ]

        filtered_results = self.repository.search(entity_ids=entity_ids)
        self.assertEqual(len(filtered_results), 1)
        self.assertIsInstance(filtered_results[0], Application)
        self.assertEqual(
            filtered_results[0].entity_id, entity_ids[0]
        )

    def test_search_assert_return_filtered_by_application_identity(self):
        filtered_results = self.repository.search(applicant_id=self.applicant_id)

        self.assertEqual(len(filtered_results), 2)
        self.assertTrue(all([
            application.applicant_id == self.applicant_id for application in filtered_results
        ]))


class ApplicationRepositorySave(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.repository = ApplicationRepository()

    def test_save_assert_created_when_new_instance(self):
        pass

    def test_save_assert_updated_when_instance_exists(self):
        pass
