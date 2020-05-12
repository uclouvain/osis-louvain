import mock
from django.test import SimpleTestCase

from base.tests.factories.user import UserFactory
from osis_role.templatetags import osis_role


class TestATagHasPerm(SimpleTestCase):
    def setUp(self):
        self.url = "https://dummy-url.com"
        self.text = "Redirect to dummy"
        self.user = UserFactory.build()

    @mock.patch("django.contrib.auth.models.User.has_perm", return_value=True)
    def test_user_has_perm_tag(self, mock_has_perm):
        expected_context = {"url": self.url, "text": self.text}

        self.assertDictEqual(
            osis_role.a_tag_has_perm(self.url, self.text, "dummy-perm", self.user),
            expected_context
        )

    @mock.patch("osis_role.errors.get_permission_error")
    @mock.patch("django.contrib.auth.models.User.has_perm", return_value=False)
    def test_user_doesnt_have_perm_tag(self, mock_has_perm, mock_get_permission_error):
        permission_error = "You don't have access to this link"
        mock_get_permission_error.return_value = permission_error

        expected_context = {
            "url": "#",
            "text": self.text,
            "class_a": "disabled",
            "error_msg": permission_error
        }
        self.assertDictEqual(
            osis_role.a_tag_has_perm(self.url, self.text, "dummy-perm", self.user),
            expected_context
        )


class TestATagModalHasPerm(SimpleTestCase):
    def setUp(self):
        self.url = "https://dummy-url.com"
        self.text = "Redirect to dummy"
        self.user = UserFactory.build()

    @mock.patch("django.contrib.auth.models.User.has_perm", return_value=True)
    def test_user_has_perm_tag(self, mock_has_perm):
        expected_context = {
            "url": self.url,
            "text": self.text,
            "class_a": "trigger_modal",
            "load_modal": True,
        }

        self.assertDictEqual(
            osis_role.a_tag_modal_has_perm(self.url, self.text, "dummy-perm", self.user),
            expected_context
        )

    @mock.patch("osis_role.errors.get_permission_error")
    @mock.patch("django.contrib.auth.models.User.has_perm", return_value=False)
    def test_user_doesnt_have_perm_tag(self, mock_has_perm, mock_get_permission_error):
        permission_error = "You don't have access to this link"
        mock_get_permission_error.return_value = permission_error

        expected_context = {
            "url": "#",
            "text": self.text,
            "class_a": "disabled",
            "error_msg": permission_error,
            "load_modal": True,
        }
        self.assertDictEqual(
            osis_role.a_tag_modal_has_perm(self.url, self.text, "dummy-perm", self.user),
            expected_context
        )


class TestHasPermTag(SimpleTestCase):
    def setUp(self):
        self.user = UserFactory.build()
        self.obj = UserFactory.build()

    @mock.patch('rules.templatetags.rules.has_perm', return_value=True)
    def test_ensure_has_perm_tag_call_django_rules(self, mock_rules_has_perm):
        self.assertTrue(
            osis_role.has_perm("dummy-perm", self.user, obj=self.obj)
        )
        mock_rules_has_perm.assert_called_once_with("dummy-perm", self.user, self.obj)


class TestHasModulePermsTag(SimpleTestCase):
    def setUp(self):
        self.user = UserFactory.build()
        self.obj = UserFactory.build()

    @mock.patch('django.contrib.auth.models._user_has_module_perms', return_value=True)
    def test_ensure_has_perm_tag_call_django_rules(self, mock_user_has_module_perms):
        self.assertTrue(osis_role.has_module_perms(self.user, "dummy-appmodule"))
        mock_user_has_module_perms.assert_called_once_with(self.user, "dummy-appmodule")
