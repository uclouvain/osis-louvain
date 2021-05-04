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
from django.core.exceptions import ObjectDoesNotExist
from django.test import TestCase

from base.tests.factories.tutor import TutorFactory
from ddd.logic.application.domain.model.applicant import ApplicantIdentity, Applicant
from infrastructure.application.repository.applicant import ApplicantRepository


class ApplicantRepositoryGet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.global_id = '7989898985'
        cls.tutor_db = TutorFactory(person__global_id=cls.global_id)
        cls.repository = ApplicantRepository()

    def test_get_assert_return_not_found(self):
        applicant_id_unknown = ApplicantIdentity(global_id="5656892656")
        with self.assertRaises(ObjectDoesNotExist):
            self.repository.get(applicant_id_unknown)

    def test_get_assert_return_instance(self):
        applicant_id = ApplicantIdentity(global_id=self.global_id)
        applicant = self.repository.get(applicant_id)

        self.assertIsInstance(applicant, Applicant)
        self.assertEqual(applicant.entity_id, applicant_id)
        self.assertEqual(applicant.first_name, self.tutor_db.person.first_name)
        self.assertEqual(applicant.last_name, self.tutor_db.person.last_name)
