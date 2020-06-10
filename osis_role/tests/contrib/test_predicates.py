from unittest import TestCase

import mock

from base.tests.factories.user import UserFactory
from osis_role import errors
from osis_role.contrib import predicates


class TestAlwaysDenyPredicate(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.user = UserFactory.build()

    def setUp(self):
        self.predicate_context_mock = mock.patch(
            "rules.Predicate.context",
            new_callable=mock.PropertyMock,
            return_value={
                'perm_name': 'dummy-perm'
            }
        )
        self.predicate_context_mock.start()
        self.addCleanup(self.predicate_context_mock.stop)

    def test_message_on_always_deny_predicate(self):
        permission_message = "Dummy message"

        self.assertFalse(predicates.always_deny(message=permission_message)(self.user))
        self.assertEqual(
            errors.get_permission_error(self.user, 'dummy-perm'),
            permission_message
        )
