############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2019 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
############################################################################
from django.test import TestCase
from django.utils.translation import gettext as _

from base.models.enums.education_group_types import GroupType
from base.models.enums.link_type import LinkTypes
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group_year import TrainingFactory, MiniTrainingFactory, \
    GroupFactory, EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from program_management.forms.group_element_year import GroupElementYearForm


class TestGroupElementYearForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        cls.parent = TrainingFactory(
            academic_year=cls.academic_year,
            education_group_type__learning_unit_child_allowed=True
        )
        cls.child_leaf = LearningUnitYearFactory()
        cls.child_branch = MiniTrainingFactory(academic_year=cls.academic_year)

    def test_fields_relevant(self):
        form = GroupElementYearForm()

        expected_fields = {
            "relative_credits",
            "is_mandatory",
            "block",
            "link_type",
            "comment",
            "comment_english",
            "access_condition"
        }
        self.assertFalse(expected_fields.symmetric_difference(set(form.fields.keys())))

    def test_clean_link_type_reference_between_eg_lu(self):
        form = GroupElementYearForm(
            data={'link_type': LinkTypes.REFERENCE.name},
            parent=self.parent,
            child_leaf=self.child_leaf
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertTrue("link_type" not in form.fields)

    def test_clean_link_type_reference_with_authorized_relationship(self):
        AuthorizedRelationshipFactory(
            parent_type=self.parent.education_group_type,
            child_type=self.child_branch.education_group_type,
        )
        ref_group = GroupElementYearFactory(
            parent=self.child_branch,
            child_branch=EducationGroupYearFactory(
                academic_year=self.academic_year,
                education_group_type=self.child_branch.education_group_type
            )
        )
        AuthorizedRelationshipFactory(
            parent_type=self.parent.education_group_type,
            child_type=ref_group.child_branch.education_group_type,
        )

        form = GroupElementYearForm(
            data={'link_type': LinkTypes.REFERENCE.name},
            parent=self.parent,
            child_branch=self.child_branch
        )

        self.assertTrue(form.is_valid())

    def test_remove_access_condition_when_not_authorized_relationship(self):
        form = GroupElementYearForm(parent=self.parent, child_branch=self.child_branch)
        self.assertTrue("access_condition" not in list(form.fields.keys()))

    def test_only_keep_access_condition_when_parent_is_minor_major_option_list_choice(self):
        expected_fields = ["access_condition"]
        for name in GroupType.minor_major_option_list_choice():
            with self.subTest(type=name):
                parent = GroupFactory(education_group_type__name=name)
                AuthorizedRelationshipFactory(
                    parent_type=parent.education_group_type,
                    child_type=self.child_branch.education_group_type
                )
                form = GroupElementYearForm(parent=parent, child_branch=self.child_branch)
                self.assertCountEqual(expected_fields, list(form.fields.keys()))

    def test_disable_all_fields_except_block_when_parent_is_formation_and_child_is_minor_major_option_list_choice(self):
        expected_fields = [
            "block"
        ]
        for name in GroupType.minor_major_option_list_choice():
            with self.subTest(type=name):
                child_branch = GroupFactory(education_group_type__name=name)
                AuthorizedRelationshipFactory(
                    parent_type=self.parent.education_group_type,
                    child_type=child_branch.education_group_type
                )
                form = GroupElementYearForm(parent=self.parent, child_branch=child_branch)
                enabled_fields = [name for name, field in form.fields.items() if not field.disabled]
                self.assertCountEqual(expected_fields, enabled_fields)

    def test_remove_access_condition_when_authorized_relationship(self):
        AuthorizedRelationshipFactory(
            parent_type=self.parent.education_group_type,
            child_type=self.child_branch.education_group_type
        )
        form = GroupElementYearForm(parent=self.parent, child_branch=self.child_branch)
        self.assertTrue("access_condition" not in list(form.fields.keys()))

    def test_child_education_group_year_without_authorized_relationship_fails(self):
        form = GroupElementYearForm(
            data={'link_type': ""},
            parent=self.parent,
            child_branch=self.child_branch
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["link_type"],
            [_("You cannot add \"%(child_types)s\" to \"%(parent)s\" (type \"%(parent_type)s\")") % {
                 'child_types': self.child_branch.education_group_type,
                 'parent': self.parent,
                 'parent_type': self.parent.education_group_type,
             }]
        )

    def test_initial_value_relative_credits(self):
        form = GroupElementYearForm(parent=self.parent, child_branch=self.child_branch)
        self.assertEqual(form.initial['relative_credits'], self.child_branch.credits)

        form = GroupElementYearForm(parent=self.parent, child_leaf=self.child_leaf)
        self.assertEqual(form.initial['relative_credits'], self.child_leaf.credits)

        form = GroupElementYearForm(parent=self.parent)
        self.assertEqual(form.initial['relative_credits'], None)
