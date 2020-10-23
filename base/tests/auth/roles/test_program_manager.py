import rules
from django.test import SimpleTestCase

from base.auth.roles.program_manager import ProgramManager
from base.models.person import Person
from education_group.auth.scope import Scope
from education_group.contrib.models import EducationGroupRoleModel
from osis_role.contrib import models as osis_role_models
from education_group.auth.roles.faculty_manager import FacultyManager


class TestProgramManager(SimpleTestCase):
    def test_class_inherit_from_education_group_role_model(self):
        self.assertTrue(issubclass(ProgramManager, EducationGroupRoleModel))

    def test_assert_group_name_meta_property(self):
        instance = ProgramManager()
        self.assertEqual(instance._meta.group_name, "program_managers")

    def test_assert_rule_sets_class_method(self):
        self.assertIsInstance(
            ProgramManager.rule_set(),
            rules.RuleSet
        )
