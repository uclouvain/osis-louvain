############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from base.models.enums.link_type import LinkTypes
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory


class TestGroupElementYearForm(TestCase):
    def setUp(self):
        self.parent = EducationGroupYearFactory()
        self.child_leaf = LearningUnitYearFactory()
        self.child_branch = EducationGroupYearFactory()

    def test_clean_link_type_reference_between_eg_lu(self):
        form = GroupElementYearForm(
            data={'link_type': LinkTypes.REFERENCE.name},
            parent=self.parent,
            child_leaf=self.child_leaf
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["link_type"],
            [_("You are not allowed to create a reference with a learning unit")]
        )

    def test_clean_link_type_reference_between_eg_without_authorized_relationship(self):
        AuthorizedRelationshipFactory(
            parent_type=self.parent.education_group_type,
            child_type=self.child_branch.education_group_type,
            reference=False
        )

        form = GroupElementYearForm(
            data={'link_type': LinkTypes.REFERENCE.name},
            parent=self.parent,
            child_branch=self.child_branch
        )

        self.assertFalse(form.is_valid())
        self.assertEqual(
            form.errors["link_type"],
            [_(
                "You are not allow to create a reference link between a %(parent_type)s and a %(child_type)s."
            ) % {
                 "parent_type": self.parent.education_group_type,
                 "child_type": self.child_branch.education_group_type,
             }]
        )

    def test_clean_link_type_reference_with_authorized_relationship(self):
        AuthorizedRelationshipFactory(
            parent_type=self.parent.education_group_type,
            child_type=self.child_branch.education_group_type,
            reference=True
        )

        form = GroupElementYearForm(
            data={'link_type': LinkTypes.REFERENCE.name},
            parent=self.parent,
            child_branch=self.child_branch
        )

        self.assertTrue(form.is_valid())

    def test_reorder_children_by_partial_acronym(self):
        group_element_1 = GroupElementYearFactory(
            child_branch__partial_acronym="SECOND",
            order=1
        )
        group_element_2 = GroupElementYearFactory(
            parent=group_element_1.parent,
            child_branch__partial_acronym="FIRST",
            order=2
        )
        GroupElementYearForm._reorder_children_by_partial_acronym(group_element_1.parent)

        group_element_1.refresh_from_db()
        group_element_2.refresh_from_db()
        self.assertTrue(
            group_element_1.order == 1 and group_element_2.order == 0
        )
