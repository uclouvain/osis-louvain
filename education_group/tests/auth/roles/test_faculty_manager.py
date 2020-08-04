import rules
from django.test import SimpleTestCase

from education_group.auth.scope import Scope
from osis_role.contrib import models as osis_role_models
from education_group.auth.roles.faculty_manager import FacultyManager


class TestFacultyManager(SimpleTestCase):
    def test_class_inherit_from_entity_role_model(self):
        self.assertTrue(issubclass(FacultyManager, osis_role_models.EntityRoleModel))

    def test_assert_group_name_meta_property(self):
        instance = FacultyManager()
        self.assertEqual(instance._meta.group_name, "faculty_managers")

    def test_assert_rule_sets_class_method(self):
        self.assertIsInstance(
            FacultyManager.rule_set(),
            rules.RuleSet
        )

    def test_get_allowed_education_group_types_one_type(self):
        faculty_manager = FacultyManager(scopes=[Scope.ALL.name])
        self.assertEqual(
            faculty_manager.get_allowed_education_group_types(),
            Scope.get_education_group_types(Scope.ALL.name)
        )

    def test_get_allowed_education_group_types_multiple_type_assert_union_of_both(self):
        faculty_manager = FacultyManager(scopes=[Scope.ALL.name, Scope.IUFC.name])
        self.assertEqual(
            faculty_manager.get_allowed_education_group_types(),
            Scope.get_education_group_types(Scope.ALL.name) + Scope.get_education_group_types(Scope.IUFC.name)
        )
