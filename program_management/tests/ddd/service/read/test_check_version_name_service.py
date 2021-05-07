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
from django.test import SimpleTestCase

from base.ddd.utils.business_validator import MultipleBusinessExceptions
from program_management.ddd import command
from program_management.ddd.domain import exception
from program_management.ddd.domain.program_tree_version import NOT_A_TRANSITION
from program_management.ddd.service.read import check_version_name_service
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionIdentityFactory
from testing.mocks import MockPatcherMixin


class TestCheckVersionName(SimpleTestCase, MockPatcherMixin):
    def setUp(self) -> None:
        self.mock_get_last_version = self.mock_service(
            "program_management.ddd.domain.service.get_last_existing_version_name."
            "GetLastExistingVersion.get_last_existing_version_identity",
            None
        )

    def test_should_check_version_name_format(self):
        cmd = command.CheckVersionNameCommand(
            year=2018,
            offer_acronym="Offer",
            version_name="VER_SION",
            transition_name=NOT_A_TRANSITION
        )

        with self.assertRaises(MultipleBusinessExceptions) as e:
            check_version_name_service.check_version_name(cmd)

        self.assertIsInstance(
            next(iter(e.exception.exceptions)),
            exception.InvalidVersionNameException
        )

    def test_should_check_if_version_name_already_exists(self):
        self.mock_get_last_version.return_value = ProgramTreeVersionIdentityFactory(year=2018)
        cmd = command.CheckVersionNameCommand(
            year=2018,
            offer_acronym="Offer",
            version_name="VERSION",
            transition_name=NOT_A_TRANSITION
        )

        with self.assertRaises(MultipleBusinessExceptions) as e:
            check_version_name_service.check_version_name(cmd)

        self.assertIsInstance(
            next(iter(e.exception.exceptions)),
            exception.VersionNameExistsCurrentYearAndInFuture
        )

    def test_should_check_if_version_name_has_existed(self):
        self.mock_get_last_version.return_value = ProgramTreeVersionIdentityFactory(year=2016)
        cmd = command.CheckVersionNameCommand(
            year=2018,
            offer_acronym="Offer",
            version_name="VERSION",
            transition_name=NOT_A_TRANSITION
        )

        with self.assertRaises(MultipleBusinessExceptions) as e:
            check_version_name_service.check_version_name(cmd)

        self.assertIsInstance(
            next(iter(e.exception.exceptions)),
            exception.VersionNameExistsInPast
        )