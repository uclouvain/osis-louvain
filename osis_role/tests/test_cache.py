from types import new_class

from django.test import SimpleTestCase, override_settings
from rules import predicate

from base.tests.factories.user import UserFactory
from osis_role import cache
from osis_role.cache import CachePredicateResultNotFound, predicate_cache


@override_settings(PERMISSION_CACHE_ENABLED=True)
class TestGetCachePredicateResult(SimpleTestCase):
    def setUp(self):
        self.user = UserFactory.build()

    def test_get_cache_predicate_result_when_no_cached_value(self):
        with self.assertRaises(CachePredicateResultNotFound):
            cache.get_cache_predicate_result(self.user, 'predicate_cache_key')

    def test_get_cache_predicate_result_when_cached_value(self):
        cached_result = True
        self.user._cache_predicates = {"predicate_cache_key": cached_result}

        self.assertEqual(
            cache.get_cache_predicate_result(self.user, 'predicate_cache_key'),
            cached_result
        )


@override_settings(PERMISSION_CACHE_ENABLED=True)
class TestSetCachePredicateResult(SimpleTestCase):
    def setUp(self):
        self.user = UserFactory.build()

    def test_set_error_perm_user(self):
        cached_result = True

        cache.set_cache_predicate_result(self.user, 'predicate_cache_key', cached_result)
        self.assertEqual(
            self.user._cache_predicates['predicate_cache_key'],
            cached_result
        )


@override_settings(PERMISSION_CACHE_ENABLED=True)
class TestPredicateCacheDecorator(SimpleTestCase):
    def setUp(self):
        self.user = UserFactory.build()

    @predicate(bind=True)
    @predicate_cache(cache_key_fn=lambda *args, **kwargs: 'predicate_cache_key')
    def predicate_name(self, user_obj, obj=None):
        return True

    def test_user_has_perm_assert_no_error_message(self):
        self.assertTrue(self.predicate_name(self.user))
        self.assertTrue(
            cache.get_cache_predicate_result(self.user, 'predicate_name_predicate_cache_key')
        )

    def test_user_has_perm_assert_no_error_message_with_obj(self):
        dummy_obj = new_class('dummy_type')()
        self.assertTrue(self.predicate_name(self.user, dummy_obj))
        self.assertTrue(
            cache.get_cache_predicate_result(self.user, 'predicate_name_dummy_type_predicate_cache_key')
        )
