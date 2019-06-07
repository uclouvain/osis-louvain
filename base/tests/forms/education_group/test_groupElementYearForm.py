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

from base.forms.education_group.group_element_year import GroupElementYearForm
from base.models.enums.education_group_types import GroupType
from base.models.enums.link_type import LinkTypes
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group_year import TrainingFactory, MiniTrainingFactory, \
    GroupFactory, EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory


class TestGroupElementYearForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()

    def setUp(self):
        self.parent = TrainingFactory(academic_year=self.academic_year)
        self.child_leaf = LearningUnitYearFactory()
        self.child_branch = MiniTrainingFactory(academic_year=self.academic_year)

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

        self.assertTrue(form.is_valid())
        self.assertTrue("link_type" not in form.fields)

    def test_clean_link_type_reference_between_eg_without_authorized_relationship(self):
        AuthorizedRelationshipFactory(
            parent_type=self.parent.education_group_type,
            child_type=self.child_branch.education_group_type,
        )
        ref_group = GroupElementYearFactory(parent=self.child_branch,
                                            child_branch=EducationGroupYearFactory(academic_year=self.academic_year))
        form = GroupElementYearForm(
            data={'link_type': LinkTypes.REFERENCE.name},
            parent=self.parent,
            child_branch=self.child_branch
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["link_type"],
            [_(
                "You cannot attach \"%(child_types)s\" to \"%(parent)s\" (type \"%(parent_type)s\")"
            ) % {
                 "parent_type": self.parent.education_group_type,
                 "parent": self.parent,
                 "child_types": ref_group.child_branch.education_group_type,
             }]
        )

    def test_clean_link_type_reference_with_authorized_relationship(self):
        AuthorizedRelationshipFactory(
            parent_type=self.parent.education_group_type,
            child_type=self.child_branch.education_group_type,
        )
        ref_group = GroupElementYearFactory(parent=self.child_branch,
                                            child_branch=EducationGroupYearFactory(academic_year=self.academic_year))
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

    def test_reorder_children_by_partial_acronym(self):
        group_element_1 = GroupElementYearFactory(
            order=1,
            parent=EducationGroupYearFactory(academic_year=self.academic_year),
            child_branch=EducationGroupYearFactory(academic_year=self.academic_year, partial_acronym="SECOND")
        )
        group_element_2 = GroupElementYearFactory(
            parent=group_element_1.parent,
            order=2,
            child_branch=EducationGroupYearFactory(academic_year=self.academic_year, partial_acronym="FIRST")
        )
        GroupElementYearForm._reorder_children_by_partial_acronym(group_element_1.parent)

        group_element_1.refresh_from_db()
        group_element_2.refresh_from_db()
        self.assertTrue(
            group_element_1.order == 1 and group_element_2.order == 0
        )

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

    def test_only_keep_block_when_parent_is_formation_and_child_is_minor_major_option_list_choice(self):
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
                self.assertCountEqual(expected_fields, list(form.fields.keys()))

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
            [_("You cannot attach \"%(child_types)s\" to \"%(parent)s\" (type \"%(parent_type)s\")") % {
                 'child_types': self.child_branch.education_group_type,
                 'parent': self.parent,
                 'parent_type': self.parent.education_group_type,
             }]
        )

    def test_referenced_child_with_max_limit(self):
        child = EducationGroupYearFactory(academic_year=self.academic_year)

        GroupElementYearFactory(
            parent=self.parent,
            child_branch=child
        )

        AuthorizedRelationshipFactory(
            parent_type=self.parent.education_group_type,
            child_type=child.education_group_type,
            max_count_authorized=1,
        )

        ref_group = GroupElementYearFactory(parent=self.child_branch,
                                            child_branch__academic_year=self.academic_year)
        AuthorizedRelationshipFactory(
            parent_type=self.parent.education_group_type,
            child_type=ref_group.child_branch.education_group_type,
        )

        ref_group.child_branch.education_group_type = child.education_group_type
        ref_group.child_branch.save()

        form = GroupElementYearForm(
            data={'link_type': LinkTypes.REFERENCE.name},
            parent=self.parent,
            child_branch=self.child_branch
        )

        self.assertFalse(form.is_valid())

        self.assertEqual(form.errors['link_type'], [
            _("The number of children of type(s) \"%(child_types)s\" for \"%(parent)s\" "
              "has already reached the limit.") % {
                'child_types': child.education_group_type,
                'parent': self.parent
            }
        ])
