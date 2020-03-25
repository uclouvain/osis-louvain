from unittest import mock

from django.contrib.auth.models import Group
from django.test import TestCase

from base.tests.factories.person import PersonFactory
from osis_role.management.commands import sync_user_role


class TestSynchonizationUserRoleCommand(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.group, _ = Group.objects.get_or_create(name="concrete_role")
        cls.command_instance = sync_user_role.Command()

    def setUp(self):
        self.person = PersonFactory()

        self.mock_role_model = mock.Mock()
        type(self.mock_role_model).group_name = mock.PropertyMock(return_value=self.group.name)
        mock_config = {'roles': {self.mock_role_model}}
        patcher_role_manager = mock.patch("osis_role.role.role_manager", **mock_config)
        patcher_role_manager.start()
        self.addCleanup(patcher_role_manager.stop)

    @mock.patch('osis_role.management.commands.sync_user_role.Command._get_users_in_role_model_but_not_in_auth_groups')
    @mock.patch('osis_role.management.commands.sync_user_role.Command._get_users_in_auth_groups_but_not_in_role_model')
    def test_synchronize_users_groups_case_group_add(self, mock_user_in_group_not_role_model,
                                                     mock_user_in_role_model_not_in_group):
        mock_user_in_group_not_role_model.return_value = []
        mock_user_in_role_model_not_in_group.return_value = [self.person.user]

        self.command_instance.handle()

        self.person.refresh_from_db()
        self.assertEquals(self.person.user.groups.count(), 1)

    @mock.patch('osis_role.management.commands.sync_user_role.Command._get_users_in_role_model_but_not_in_auth_groups')
    @mock.patch('osis_role.management.commands.sync_user_role.Command._get_users_in_auth_groups_but_not_in_role_model')
    def test_synchronize_users_groups_case_group_remove(self, mock_user_in_group_not_role_model,
                                                        mock_user_in_role_model_not_in_group):
        self.person.user.groups.add(self.group)
        mock_user_in_group_not_role_model.return_value = [self.person.user]
        mock_user_in_role_model_not_in_group.return_value = []

        self.command_instance.handle()
        self.person.refresh_from_db()
        self.assertEquals(self.person.user.groups.count(), 0)
