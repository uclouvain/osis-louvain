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

from base.tests.factories.education_group_year import EducationGroupYearFactory
from education_group.ddd.domain.service.link_with_epc import LinkWithEPC
from education_group.tests.ddd.factories.training import TrainingIdentityFactory


class TestLinkWithEPC(TestCase):
    def test_should_return_false_when_training_does_not_exist(self):
        identity = TrainingIdentityFactory()

        result = LinkWithEPC().is_training_have_link_with_epc(identity)

        self.assertFalse(result)

    def test_should_return_false_when_training_is_not_linked_to_epc(self):
        identity = TrainingIdentityFactory()
        EducationGroupYearFactory(acronym=identity.acronym, academic_year__year=identity.year)

        result = LinkWithEPC().is_training_have_link_with_epc(identity)

        self.assertFalse(result)

    def test_should_return_true_when_training_is_linked_to_epc(self):
        identity = TrainingIdentityFactory()
        EducationGroupYearFactory(acronym=identity.acronym, academic_year__year=identity.year, linked_with_epc=True)

        result = LinkWithEPC().is_training_have_link_with_epc(identity)

        self.assertTrue(result)
