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
from mock import mock

from education_group.ddd.command import GetGroupIssueFieldsOnWarningCommand
from education_group.ddd.domain import exception
from education_group.ddd.factories.group import GroupFactory
from education_group.ddd.service.read.check_group_issue_fields_on_warning_service import \
    check_group_issue_fields_on_warning
from education_group.tests.ddd.factories.repository.fake import get_fake_group_repository
from testing.mocks import MockPatcherMixin


class TestCheckIssueFields(SimpleTestCase, MockPatcherMixin):
    def setUp(self):
        self.group = GroupFactory()
        fake_group_repository = get_fake_group_repository([self.group])
        self.mock_repo("education_group.ddd.repository.group.GroupRepository", fake_group_repository)

        self.command = GetGroupIssueFieldsOnWarningCommand(
            code=self.group.entity_id.code,
            year=self.group.entity_id.year
        )

        self.mock_service(
            "education_group.ddd.domain.service.fields_with_alert_when_issue.get_for_group",
            ["management_entity"]
        )

    @mock.patch(
        'education_group.ddd.domain.service.get_entity_active.ActiveEntity.is_entity_active_for_year',
        return_value=True
    )
    def test_should_not_return_exception_when_no_empty_fields(self, mock_get_entity_active):
        result = check_group_issue_fields_on_warning(self.command)

        self.assertEqual(result, None)

    @mock.patch(
        'education_group.ddd.domain.service.get_entity_active.ActiveEntity.is_entity_active_for_year',
        return_value=False
    )
    def test_should_raise_exception_when_empty_fields(self, mock_get_entity_active):
        with self.assertRaises(exception.GroupAlertFieldException):
            check_group_issue_fields_on_warning(self.command)
