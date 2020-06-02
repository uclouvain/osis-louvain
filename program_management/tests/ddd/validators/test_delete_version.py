##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
##############################################################################


from django.test import TestCase

from base.models.enums.education_group_types import GroupType
from base.models.group_element_year import GroupElementYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.offer_enrollment import OfferEnrollmentFactory
from education_group.models.group_year import GroupYear
from education_group.tests.factories.group_year import GroupYearFactory, TrainingGroupYearFactory
from program_management.ddd.repositories.program_tree_version import _delete_version_root_group
from program_management.ddd.validators._delete_version import NoEnrollmentValidator
from program_management.ddd.domain.service.tree_has_contents import have_contents_which_are_not_mandatory
from program_management.tests.ddd.service.write.test_delete_program_tree_version_service import build_version_content, \
    EDUCATION_GROUP_VERSION
from program_management.tests.factories.element import ElementGroupYearFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory

from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository, ProgramTreeVersionIdentity
from program_management.ddd.validators._delete_version import EmptyTreeValidator


class TestDeleteVersionValidator(TestCase):

    def setUp(self):
        """
            (education_group_version)
            root_node
            |-link_level_1
              |-link_level_2
                |-- leaf
        """
        self.data = {}
        self.academic_year = AcademicYearFactory()
        self.previous_academic_year = AcademicYearFactory(year=self.academic_year.year - 1)
        self.next_academic_year = AcademicYearFactory(year=self.academic_year.year+1)

        self.data.update(build_version_content(self.academic_year))
        self.data.update(build_version_content(self.next_academic_year))
        self.data.update(build_version_content(self.previous_academic_year))

    def test_validator_has_no_offer_enrollments(self):
        empty_tree_version = EducationGroupVersionFactory(
            root_group__academic_year=self.academic_year,
            root_group__group__start_year=self.academic_year,
            offer__academic_year=self.academic_year,
        )
        validator = NoEnrollmentValidator(education_group_versions=[empty_tree_version])
        self.assertTrue(validator.is_valid())
        self.assertEqual(len(validator.messages), 0)

    def test_validator_has_offer_enrollments(self):
        education_group_version = self.data.get(self.academic_year).get(EDUCATION_GROUP_VERSION)
        OfferEnrollmentFactory.create_batch(
            3,
            education_group_year=education_group_version.offer,
        )

        education_group_version = self.data.get(self.academic_year).get(EDUCATION_GROUP_VERSION)
        validator = NoEnrollmentValidator(education_group_versions=[education_group_version])
        self.assertFalse(validator.is_valid())
        self.assertEqual(len(validator.messages), 1)


class TestHaveContents(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2019)

    def test_have_contents_case_no_contents(self):
        group_year = TrainingGroupYearFactory(academic_year=self.academic_year)
        self.assertFalse(have_contents_which_are_not_mandatory(group_year))

    def test_have_contents_case_no_contents_which_because_mandatory_structure(self):
        """
        In this test, we ensure that all of his children are mandatory groups and they are empty.
        It must be consider as empty
        """

        group_year = TrainingGroupYearFactory(academic_year=self.academic_year, group__start_year=self.academic_year)

        element_group_year = ElementGroupYearFactory(group_year=group_year)
        for education_group_type in [GroupType.COMMON_CORE.name, GroupType.FINALITY_120_LIST_CHOICE.name]:

            child = GroupYearFactory(academic_year=self.academic_year,
                                     education_group_type__name=education_group_type,
                                     group__start_year=self.academic_year)
            child_element = ElementGroupYearFactory(group_year=child)

            AuthorizedRelationshipFactory(
                parent_type=group_year.education_group_type,
                child_type=child.education_group_type,
                min_count_authorized=1,
            )

            GroupElementYearFactory(parent=None, child_branch=None,
                                    parent_element=element_group_year, child_element=child_element)
        self.assertFalse(have_contents_which_are_not_mandatory(group_year))

    def test_have_contents_case_have_contents_because_mandatory_structure_is_present_multiple_times(self):
        """
        In this test, we ensure that we have two elements of one type which are mandatory in the basic structure.
        ==> We must consider as it have contents
        """

        group_yr = TrainingGroupYearFactory(academic_year=self.academic_year, group__start_year=self.academic_year)
        parent_education_group_year = ElementGroupYearFactory(group_year=group_yr)
        subgroup_1 = GroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__name=GroupType.SUB_GROUP.name,
            group__start_year=self.academic_year,
        )
        child_subgroup1 = ElementGroupYearFactory(group_year=subgroup_1)
        GroupElementYearFactory(parent_element=parent_education_group_year,
                                child_element=child_subgroup1,
                                parent=None,
                                child_branch=None)

        subgroup_2 = GroupYearFactory(
            academic_year=self.academic_year,
            education_group_type=subgroup_1.education_group_type,
            group__start_year=self.academic_year,
        )
        elt_subgroup_2 = ElementGroupYearFactory(group_year=subgroup_2)
        GroupElementYearFactory(
            parent_element=parent_education_group_year,
            child_element=elt_subgroup_2,
            parent=None,
            child_branch=None
        )

        AuthorizedRelationshipFactory(
            parent_type=group_yr.education_group_type,
            child_type=subgroup_1.education_group_type,
            min_count_authorized=1,
        )
        self.assertTrue(have_contents_which_are_not_mandatory(group_yr))

    def test_have_contents_case_contents_because_structure_have_child_which_are_not_mandatory(self):
        """
        In this test, we ensure that at least one children are not mandatory groups so they must not be considered
        as empty
        """
        group_year = TrainingGroupYearFactory(academic_year=self.academic_year, group__start_year=self.academic_year)
        parent_education_group_year = ElementGroupYearFactory(group_year=group_year)
        child_mandatory = GroupYearFactory(academic_year=self.academic_year, group__start_year=self.academic_year)
        child_mandataory_eleem = ElementGroupYearFactory(group_year=child_mandatory)
        AuthorizedRelationshipFactory(
            parent_type=group_year.education_group_type,
            child_type=child_mandatory.education_group_type,
            min_count_authorized=1
        )
        GroupElementYearFactory(
            parent_element=parent_education_group_year,
            child_element=child_mandataory_eleem,
            parent=None,
            child_branch=None,
        )

        child_no_mandatory = GroupYearFactory(academic_year=self.academic_year, group__start_year=self.academic_year)
        child_no_mandataory_eleem = ElementGroupYearFactory(group_year=child_no_mandatory)
        AuthorizedRelationshipFactory(
            parent_type=group_year.education_group_type,
            child_type=child_mandatory.education_group_type,
            min_count_authorized=0
        )
        GroupElementYearFactory(
            parent_element=parent_education_group_year,
            child_element=child_no_mandataory_eleem,
            parent=None,
            child_branch=None,
        )
        self.assertTrue(have_contents_which_are_not_mandatory(group_year))


class TestRunDelete(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(year=2019)

    def test_delete_case_no_mandatory_structure(self):

        group_yr = TrainingGroupYearFactory(academic_year=self.academic_year)
        education_group_version = EducationGroupVersionFactory(root_group=group_yr)
        _delete_version_root_group(education_group_version)
        with self.assertRaises(GroupYear.DoesNotExist):
            GroupYear.objects.get(pk=group_yr.pk)

    def test_delete_case_remove_mandatory_structure(self):
        group_yr = TrainingGroupYearFactory(academic_year=self.academic_year,
                                            group__start_year=self.academic_year)
        education_group_version = EducationGroupVersionFactory(root_group=group_yr,
                                                               offer__academic_year=self.academic_year)
        parent_element_education_group_year = ElementGroupYearFactory(group_year=group_yr)
        child_mandatory = GroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__name=GroupType.COMMON_CORE.name,
            group__start_year=self.academic_year
        )
        child_element_education_group_year = ElementGroupYearFactory(group_year=child_mandatory)
        AuthorizedRelationshipFactory(
            parent_type=group_yr.education_group_type,
            child_type=child_mandatory.education_group_type,
            min_count_authorized=1,
        )
        link_parent_child = GroupElementYearFactory(parent_element=parent_element_education_group_year,
                                                    child_element=child_element_education_group_year,
                                                    parent=None,
                                                    child_branch=None)

        identity = ProgramTreeVersionIdentity(
                education_group_version.offer.acronym,
                education_group_version.offer.academic_year.year,
                education_group_version.version_name,
                education_group_version.is_transition
            )

        ProgramTreeVersionRepository().delete(entity_id=identity)



        # _delete_version_trees([education_group_version])

        with self.assertRaises(GroupYear.DoesNotExist):
            GroupYear.objects.get(pk=group_yr.pk)
        with self.assertRaises(GroupYear.DoesNotExist):
            GroupYear.objects.get(pk=child_mandatory.pk)
        with self.assertRaises(GroupElementYear.DoesNotExist):
            GroupElementYear.objects.get(pk=link_parent_child.pk)

    def test_delete_case_remove_mandatory_structure_case_reused_item_which_are_mandatory(self):
        """
        In this test, we ensure that the mandatory elem is not removed if it is reused in another structure
        """

        root_group = TrainingGroupYearFactory(academic_year=self.academic_year, group__start_year=self.academic_year)
        root_group_element = ElementGroupYearFactory(group_year=root_group)
        education_group_version = EducationGroupVersionFactory(root_group=root_group,
                                                               offer__academic_year=self.academic_year)
        child_mandatory = GroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__name=GroupType.COMMON_CORE.name,
            group__start_year=self.academic_year
        )
        child_mandatory_element = ElementGroupYearFactory(group_year=child_mandatory)

        AuthorizedRelationshipFactory(
            parent_type=root_group.education_group_type,
            child_type=child_mandatory.education_group_type,
            min_count_authorized=1,
        )
        link_parent_child = GroupElementYearFactory(parent_element=root_group_element,
                                                    child_element=child_mandatory_element,
                                                    parent=None,
                                                    child_branch=None)

        # Create another training
        another_training = TrainingGroupYearFactory(academic_year=self.academic_year)
        another_parent_element_training = ElementGroupYearFactory(group_year=another_training)
        GroupElementYearFactory(parent_element=another_parent_element_training,
                                child_element=child_mandatory_element,
                                parent=None,
                                child_branch=None)

        identity = ProgramTreeVersionIdentity(
                education_group_version.offer.acronym,
                education_group_version.offer.academic_year.year,
                education_group_version.version_name,
                education_group_version.is_transition
            )

        ProgramTreeVersionRepository().delete(entity_id=identity)
        with self.assertRaises(GroupYear.DoesNotExist):
            GroupYear.objects.get(pk=root_group.pk)
        with self.assertRaises(GroupElementYear.DoesNotExist):
            GroupElementYear.objects.get(pk=link_parent_child.pk)

        self.assertEqual(
            child_mandatory,
            GroupYear.objects.get(pk=child_mandatory.pk)
        )
