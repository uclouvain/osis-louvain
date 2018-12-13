##############################################################################
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
###########################################################################
from django.test import TestCase

from base.business.group_element_years.management import is_max_child_reached, is_min_child_reached
from base.models.enums import count_constraint
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory


class TestChildReachedMixin():
    @classmethod
    def setUpTestData(cls):
        cls.parent_type = EducationGroupTypeFactory()
        cls.child_type = EducationGroupTypeFactory()

        cls.parent_egy = EducationGroupYearFactory(education_group_type=cls.parent_type)
        cls.child_egy = EducationGroupYearFactory(education_group_type=cls.child_type)

    def create_group_element_years_of_child_type(self):
        return GroupElementYearFactory(
            parent=self.parent_egy,
            child_branch__education_group_type=self.child_type
        )

    def create_authorized_relationship(self, max_count=count_constraint.MANY, min_count=count_constraint.ZERO):
        return AuthorizedRelationshipFactory(
            parent_type=self.parent_type,
            child_type=self.child_type,
            max_count_authorized=max_count,
            min_count_authorized=min_count,
        )


class TestIsMaxChildReached(TestChildReachedMixin, TestCase):
    def test_when_no_authorized_relationship(self):
        self.assertTrue(is_max_child_reached(self.parent_egy, self.child_egy))

    def test_should_return_false_if_no_group_element_years_of_child_type_and_max_count_set_to_one(self):
        GroupElementYearFactory(parent=self.parent_egy)
        self.create_authorized_relationship(max_count=count_constraint.ONE)
        self.assertFalse(is_max_child_reached(self.parent_egy, self.child_egy))

    def test_should_return_false_if_no_group_element_years_child_type_and_max_count_set_to_many(self):
        self.create_authorized_relationship(max_count=count_constraint.MANY)
        self.assertFalse(is_max_child_reached(self.parent_egy, self.child_egy))

    def test_should_return_true_if_one_group_element_years_child_type_and_max_count_set_to_one(self):
        self.create_group_element_years_of_child_type()
        self.create_authorized_relationship(max_count=count_constraint.ONE)
        self.assertTrue(is_max_child_reached(self.parent_egy, self.child_egy))

    def test_should_return_false_if_multiple_group_element_years_of_child_type_and_max_count_set_to_many(self):
        self.create_group_element_years_of_child_type()
        self.create_group_element_years_of_child_type()
        self.create_authorized_relationship(max_count=count_constraint.MANY)
        self.assertFalse(is_max_child_reached(self.parent_egy, self.child_egy))


class TestIsMinChildReached(TestChildReachedMixin, TestCase):
    def test_when_no_authorized_relationship(self):
        self.assertTrue(is_min_child_reached(self.parent_egy, self.child_egy))

    def test_should_return_true_if_no_group_element_years_of_child_type_and_min_count_set_to_zero(self):
        GroupElementYearFactory(parent=self.parent_egy)
        self.create_authorized_relationship(min_count=count_constraint.ZERO)
        self.assertFalse(is_min_child_reached(self.parent_egy, self.child_egy))

    def test_should_return_true_if_no_group_element_years_child_type_and_min_count_set_to_one(self):
        self.create_authorized_relationship(min_count=count_constraint.ONE)
        self.assertTrue(is_min_child_reached(self.parent_egy, self.child_egy))

    def test_should_return_false_if_one_group_element_year_of_child_type_and_min_count_set_to_zero(self):
        self.create_group_element_years_of_child_type()
        self.create_authorized_relationship(min_count=count_constraint.ZERO)
        self.assertFalse(is_min_child_reached(self.parent_egy, self.child_egy))

    def test_should_return_true_if_one_group_element_years_of_child_type_and_min_count_set_to_one(self):
        self.create_group_element_years_of_child_type()
        self.create_authorized_relationship(min_count=count_constraint.ONE)
        self.assertTrue(is_min_child_reached(self.parent_egy, self.child_egy))

    def test_should_return_false_if_multiple_group_element_years_of_child_type_and_min_count_set_to_one(self):
        self.create_group_element_years_of_child_type()
        self.create_group_element_years_of_child_type()
        self.create_authorized_relationship(min_count=count_constraint.ONE)
        self.assertFalse(is_min_child_reached(self.parent_egy, self.child_egy))
