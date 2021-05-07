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

from django.test import TestCase

from program_management.ddd.validators import _update_check_existence_of_transition
from program_management.tests.ddd.factories.program_tree_version import StandardProgramTreeVersionFactory, \
    StandardTransitionProgramTreeVersionFactory
from program_management.tests.ddd.validators.mixins import TestValidatorValidateMixin
from program_management.tests.factories.education_group_version import StandardTransitionEducationGroupVersionFactory


class TestValidateExistenceOfTransition(TestValidatorValidateMixin, TestCase):
    def setUp(self) -> None:
        self.year = 2019
        self.tree_version = StandardProgramTreeVersionFactory(
            end_year_of_existence=2019,
            entity_id__year=2019,
        )
        self.transition = StandardTransitionProgramTreeVersionFactory(
            entity_id__offer_acronym=self.tree_version.entity_id.offer_acronym,
            entity_id__year=self.year
        )

    def test_should_raise_exception_if_other_transition_in_future(self):
        StandardTransitionEducationGroupVersionFactory(
            root_group__academic_year__year=self.year + 2,
            offer__acronym=self.tree_version.entity_id.offer_acronym,
        )
        self.transition.end_year_of_existence = self.year + 4

        self.assertValidatorRaises(
            _update_check_existence_of_transition.CheckExistenceOfTransition(
                self.transition.end_year_of_existence,
                self.year,
                self.tree_version.entity_identity.offer_acronym,
                self.transition.version_name,
                self.transition.transition_name,
            ),
            None
        )

    def test_should_not_raise_exception_if_no_transition_in_future(self):
        self.transition.end_year_of_existence = self.year + 4

        self.assertValidatorNotRaises(
            _update_check_existence_of_transition.CheckExistenceOfTransition(
                self.transition.end_year_of_existence,
                self.year,
                self.tree_version.entity_identity.offer_acronym,
                self.transition.version_name,
                self.transition.transition_name,
            )
        )
