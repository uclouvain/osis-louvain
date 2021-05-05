##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase

from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from education_group.ddd.domain.service.enrollment_counter import EnrollmentCounter
from education_group.tests.ddd.factories.training import TrainingIdentityFactory


class TestEnrollmentCounter(TestCase):
    def test_should_return_0_when_no_offer_enrollments_for_training(self):
        identity = TrainingIdentityFactory()

        result = EnrollmentCounter().get_training_enrollments_count(identity)

        self.assertEqual(0, result)

    def test_should_return_number_of_enrollements_for_training(self):
        identity = TrainingIdentityFactory()
        OfferEnrollmentFactory.create_batch(
            4,
            education_group_year__acronym=identity.acronym,
            education_group_year__academic_year__year=identity.year,
            education_group_year__partial_acronym="LOPES54"
        )

        result = EnrollmentCounter().get_training_enrollments_count(identity)

        self.assertEqual(4, result)
