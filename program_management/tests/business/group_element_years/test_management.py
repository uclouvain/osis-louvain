##############################################################################
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
###########################################################################

from django.test import TestCase

from base.models.enums.link_type import LinkTypes
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from program_management.business.group_element_years.management import \
    _compute_number_children_by_education_group_type, CheckAuthorizedRelationshipDetach, \
    CheckAuthorizedRelationshipAttach


class TestAuthorizedRelationshipCheck(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.education_group_types = EducationGroupTypeFactory.create_batch(3)

        cls.parent_egy = EducationGroupYearFactory()

        cls.grp_type_1 = GroupElementYearFactory(
            parent=cls.parent_egy,
            child_branch__education_group_type=cls.education_group_types[0],
            child_branch__academic_year=cls.parent_egy.academic_year
        )
        GroupElementYearFactory.create_batch(
            2,
            parent=cls.parent_egy,
            child_branch__education_group_type=cls.education_group_types[1],
            child_branch__academic_year=cls.parent_egy.academic_year
        )
        cls.reference_group_element_year_children = GroupElementYearFactory(
            parent=cls.parent_egy,
            child_branch__education_group_type=cls.education_group_types[0],
            child_branch__academic_year=cls.parent_egy.academic_year,
            link_type=LinkTypes.REFERENCE.name
        )

        GroupElementYearFactory.create_batch(
            2,
            parent=cls.reference_group_element_year_children.child_branch,
            child_branch__education_group_type=cls.education_group_types[1],
            child_branch__academic_year=cls.reference_group_element_year_children.child_branch.academic_year
        )
        GroupElementYearFactory(
            parent=cls.reference_group_element_year_children.child_branch,
            child_branch__education_group_type=cls.education_group_types[2],
            child_branch__academic_year=cls.reference_group_element_year_children.child_branch.academic_year
        )

        cls.child = EducationGroupYearFactory(education_group_type=cls.education_group_types[0])
        GroupElementYearFactory.create_batch(
            2,
            parent=cls.child,
            child_branch__education_group_type=cls.education_group_types[2],
            child_branch__academic_year=cls.child.academic_year,
        )

        AuthorizedRelationshipFactory(
            parent_type=cls.parent_egy.education_group_type,
            child_type=cls.education_group_types[0],
            min_count_authorized=1,
            max_count_authorized=1
        )
        AuthorizedRelationshipFactory(
            parent_type=cls.parent_egy.education_group_type,
            child_type=cls.education_group_types[1],
            min_count_authorized=0,
            max_count_authorized=None
        )

    def test_when_min_reached_after_detaching(self):
        check = CheckAuthorizedRelationshipDetach(
            self.parent_egy,
            link_to_detach=self.grp_type_1
        )
        self.assertFalse(check.is_valid())

    def test_when_max_reached_after_attaching(self):
        link_to_attach = GroupElementYearFactory.build(
            parent=self.parent_egy,
            child_branch=EducationGroupYearFactory(
                education_group_type=self.education_group_types[0]
            )
        )
        check = CheckAuthorizedRelationshipAttach(
            self.parent_egy,
            link_to_attach=link_to_attach
        )
        self.assertFalse(check.is_valid())

    def test_when_update_an_existing_instance(self):
        link_to_attach = self.grp_type_1
        check = CheckAuthorizedRelationshipAttach(
            self.parent_egy,
            link_to_attach=link_to_attach
        )
        self.assertTrue(check.is_valid())

    def test_when_child_not_authorized_for_attach(self):
        link_to_attach = GroupElementYearFactory.build(
            parent=self.parent_egy,
            child_branch=EducationGroupYearFactory(
                education_group_type=self.education_group_types[2]
            )
        )
        check = CheckAuthorizedRelationshipAttach(
            self.parent_egy,
            link_to_attach=link_to_attach
        )
        self.assertFalse(check.is_valid())

    def test_when_detaching_should_succeed(self):
        check = CheckAuthorizedRelationshipDetach(
            self.parent_egy,
            link_to_detach=self.reference_group_element_year_children
        )
        self.assertTrue(check.is_valid())


class TestComputeNumberChildrenByEducationGroupType(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.parent_egy = EducationGroupYearFactory()
        cls.education_group_types = EducationGroupTypeFactory.create_batch(3)
        GroupElementYearFactory.create_batch(
            3,
            parent=cls.parent_egy,
            child_branch__education_group_type=cls.education_group_types[0],
            child_branch__academic_year=cls.parent_egy.academic_year
        )
        GroupElementYearFactory.create_batch(
            2,
            parent=cls.parent_egy,
            child_branch__education_group_type=cls.education_group_types[1],
            child_branch__academic_year=cls.parent_egy.academic_year
        )
        GroupElementYearChildLeafFactory.create_batch(
            2,
            parent=cls.parent_egy
        )

        cls.reference_group_element_year_children = GroupElementYearFactory(
            parent=cls.parent_egy,
            child_branch__education_group_type=cls.education_group_types[0],
            child_branch__academic_year=cls.parent_egy.academic_year,
            link_type=LinkTypes.REFERENCE.name
        )
        GroupElementYearFactory.create_batch(
            2,
            parent=cls.reference_group_element_year_children.child_branch,
            child_branch__education_group_type=cls.education_group_types[1],
            child_branch__academic_year=cls.reference_group_element_year_children.child_branch.academic_year
        )
        GroupElementYearFactory(
            parent=cls.reference_group_element_year_children.child_branch,
            child_branch__education_group_type=cls.education_group_types[2],
            child_branch__academic_year=cls.reference_group_element_year_children.child_branch.academic_year
        )

        cls.child = EducationGroupYearFactory(education_group_type=cls.education_group_types[0])
        GroupElementYearFactory.create_batch(
            2,
            parent=cls.child,
            child_branch__education_group_type=cls.education_group_types[2],
            child_branch__academic_year=cls.child.academic_year,
        )

    def test_when_no_children(self):
        parent_without_children = EducationGroupYearFactory()

        expected_result = [
            self._create_result_record(self.education_group_types[0], 1)
        ]
        link = GroupElementYearFactory.build(child_branch=self.child, link_type=None)
        self.assertCountEqual(
            list(_compute_number_children_by_education_group_type(parent_without_children, link)),
            expected_result
        )

    def test_when_children(self):
        expected_result = [
            self._create_result_record(self.education_group_types[0], 3 + 1),
            self._create_result_record(self.education_group_types[1], 4),
            self._create_result_record(self.education_group_types[2], 1)
        ]
        link = GroupElementYearFactory.build(child_branch=self.child, link_type=None)
        self.assertCountEqual(
            list(_compute_number_children_by_education_group_type(self.parent_egy, link)),
            expected_result
        )
        AuthorizedRelationshipFactory(parent_type=self.parent_egy.education_group_type,
                                      child_type=self.child.education_group_type)

    def test_when_children_with_link_reference(self):
        expected_result = [
            self._create_result_record(self.education_group_types[0], 3),
            self._create_result_record(self.education_group_types[1], 4),
            self._create_result_record(self.education_group_types[2], 1 + 2)
        ]
        link = GroupElementYearFactory.build(child_branch=self.child, link_type=LinkTypes.REFERENCE.name)
        self.assertCountEqual(
            list(_compute_number_children_by_education_group_type(self.parent_egy, link)),
            expected_result
        )

    def test_when_switching_link_type_of_existing_child(self):
        expected_result = [
            self._create_result_record(self.education_group_types[0], 3 + 1),
            self._create_result_record(self.education_group_types[1], 4 - 2)
        ]

        link = GroupElementYearFactory.build(child_branch=self.reference_group_element_year_children.child_branch,
                                             link_type=None)
        self.assertCountEqual(
            list(_compute_number_children_by_education_group_type(self.parent_egy, link)),
            expected_result
        )

    def test_when_deleting_link(self):
        expected_result = [
            self._create_result_record(self.education_group_types[0], 3),
            self._create_result_record(self.education_group_types[1], 4 - 2)
        ]

        link = self.reference_group_element_year_children
        self.assertCountEqual(
            list(_compute_number_children_by_education_group_type(self.parent_egy, link, to_delete=True)),
            expected_result
        )

    def _create_result_record(self, education_group_type, count):
        return {
            "education_group_type__name": education_group_type.name,
            "count": count
        }
