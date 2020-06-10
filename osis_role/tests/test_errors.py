import mock
from django.test import SimpleTestCase
from rules import predicate

from base.tests.factories.user import UserFactory
from osis_role import errors


class TestClearPermissionError(SimpleTestCase):
    def setUp(self):
        self.user = UserFactory.build()

    def test_clear_cache_case_user_have_no_error_in_stack(self):
        errors.clear_permission_error(self.user, 'dummy-perm')

    def test_clear_cache_case_user_have_error_in_stack(self):
        self.user._cached_error_perms = {
            "dummy-perm": "You don't have access to this feature"
        }
        errors.clear_permission_error(self.user, 'dummy-perm')

        self.assertIsNone(self.user._cached_error_perms["dummy-perm"])


class TestGetPermissionError(SimpleTestCase):
    def setUp(self):
        self.user = UserFactory.build()

    def test_get_error_perm_user_have_no_error_in_stack(self):
        self.assertIsNone(
            errors.get_permission_error(self.user, 'dummy-perm')
        )

    def test_get_error_perm_user_have_error_in_stack(self):
        permission_error = "You don't have access to this feature"
        self.user._cached_error_perms = {"dummy-perm": permission_error}

        self.assertEqual(errors.get_permission_error(self.user, 'dummy-perm'), permission_error)


class TestSetPermissionError(SimpleTestCase):
    def setUp(self):
        self.user = UserFactory.build()

    def test_set_error_perm_user(self):
        permission_error = "You don't have access to this feature"

        errors.set_permission_error(self.user, 'dummy-perm', permission_error)
        self.assertEqual(
            self.user._cached_error_perms['dummy-perm'],
            permission_error
        )


class TestPredicateFailedMessageDecorator(SimpleTestCase):
    def setUp(self):
        self.user = UserFactory.build()
        self.predicate_context_mock = mock.patch(
            "rules.Predicate.context",
            new_callable=mock.PropertyMock,
            return_value={
                'perm_name': 'dummy-perm'
            }
        )
        self.predicate_context_mock.start()
        self.addCleanup(self.predicate_context_mock.stop)

    def test_user_has_perm_assert_no_error_message(self):
        @predicate(bind=True)
        @errors.predicate_failed_msg(message="Access Denied")
        def pred(self, user, obj=None):
            return True

        self.assertTrue(pred(self.user))
        self.assertIsNone(errors.get_permission_error(self.user, 'dummy-perm'))

    def test_user_hasnt_perm_assert_error_message(self):
        @predicate(bind=True)
        @errors.predicate_failed_msg(message="Access Denied")
        def pred(self, user, obj=None):
            return False

        self.assertFalse(pred(self.user))
        self.assertEqual(
            errors.get_permission_error(self.user, 'dummy-perm'),
            "Access Denied"
        )

    def test_skip_predicate_dont_store_error_message(self):
        @predicate(bind=True)
        @errors.predicate_failed_msg(message="Access Denied")
        def pred(self, user, obj=None):
            return None

        self.assertIsNone(pred(self.user))
        self.assertIsNone(errors.get_permission_error(self.user, 'dummy-perm'))
