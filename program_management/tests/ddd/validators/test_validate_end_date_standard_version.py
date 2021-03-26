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

import attr
from django.test import TestCase

from base.tests.factories.academic_year import AcademicYearFactory
from program_management.ddd.validators import _delete_check_versions_end_date
from program_management.tests.ddd.factories.program_tree_version import SpecificProgramTreeVersionFactory, \
    StandardProgramTreeVersionFactory
from program_management.tests.ddd.validators.mixins import TestValidatorValidateMixin
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory


class CheckVersionEndDateValidatorForStandardTest(TestCase, TestValidatorValidateMixin):
    @classmethod
    def setUpTestData(cls):
        cls.standard_version = StandardProgramTreeVersionFactory()

    def test_should_be_valid_when_no_version_associated_to_standard(self):
        validator = _delete_check_versions_end_date.CheckVersionsEndDateValidator(self.standard_version)

        self.assertValidatorNotRaises(validator)

    def test_should_be_valid_when_no_version_exists_during_the_standard_year(self):
        self._create_version_with_inferior_end_date()

        validator = _delete_check_versions_end_date.CheckVersionsEndDateValidator(self.standard_version)

        self.assertValidatorNotRaises(validator)

    def test_should_not_be_valid_when_specific_version_exists_during_the_standard_year(self):
        self._create_version_with_superior_end_date()

        validator = _delete_check_versions_end_date.CheckVersionsEndDateValidator(self.standard_version)

        self.assertValidatorRaises(validator, None)

    def test_should_not_be_valid_when_transition_version_exists_during_the_standard_year(self):
        self._create_transition_version_with_superior_end_date()

        validator = _delete_check_versions_end_date.CheckVersionsEndDateValidator(self.standard_version)

        self.assertValidatorRaises(validator, None)

    def test_should_always_be_valid_for_specific_version(self):
        tree_version = SpecificProgramTreeVersionFactory(
            entity_id=attr.evolve(self.standard_version.entity_id, version_name="SPECIFIC")
        )

        self._create_version_with_superior_end_date()

        validator = _delete_check_versions_end_date.CheckVersionsEndDateValidator(tree_version)

        self.assertValidatorNotRaises(validator)

    def _create_version_with_inferior_end_date(self):
        anac = AcademicYearFactory(year=self.standard_version.entity_id.year - 1)
        EducationGroupVersionFactory(
            offer__acronym=self.standard_version.entity_id.offer_acronym,
            offer__academic_year=anac,
            offer__education_group__end_year=anac,
            root_group__group__start_year=anac,
            root_group__group__end_year=anac,
            root_group__academic_year=anac
        )

    def _create_version_with_superior_end_date(self):
        EducationGroupVersionFactory(
            offer__acronym=self.standard_version.entity_id.offer_acronym,
            offer__academic_year__year=self.standard_version.entity_id.year + 1,
            offer__education_group__end_year=None,
            root_group__group__end_year=None,
        )

    def _create_transition_version_with_superior_end_date(self):
        EducationGroupVersionFactory(
            offer__acronym=self.standard_version.entity_id.offer_acronym,
            offer__academic_year__year=self.standard_version.entity_id.year + 1,
            offer__education_group__end_year=None,
            root_group__group__end_year=None,
            transition_name="TRANSITION"
        )
