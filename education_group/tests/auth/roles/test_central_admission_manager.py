import rules
from django.test import SimpleTestCase

from education_group.auth.roles.central_admission_manager import CentralAdmissionManager
from osis_role.contrib import models as osis_role_models


class TestCentralAdmissionManager(SimpleTestCase):
    def test_class_inherit_from_role_model(self):
        self.assertTrue(issubclass(CentralAdmissionManager, osis_role_models.RoleModel))

    def test_assert_group_name_meta_property(self):
        instance = CentralAdmissionManager()
        self.assertEqual(instance._meta.group_name, "central_admission_managers")

    def test_assert_rule_sets_class_method(self):
        self.assertIsInstance(
            CentralAdmissionManager.rule_set(),
            rules.RuleSet
        )
