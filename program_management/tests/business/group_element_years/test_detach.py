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
##############################################################################
from unittest import mock

from django.test import TestCase

from base.models.enums import education_group_types
from base.models.enums.education_group_types import TrainingType, GroupType, MiniTrainingType
from base.models.prerequisite import Prerequisite
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import TrainingFactory, GroupFactory, MiniTrainingFactory
from base.tests.factories.group_element_year import GroupElementYearFactory, GroupElementYearChildLeafFactory
from base.tests.factories.prerequisite import PrerequisiteFactory
from base.tests.factories.prerequisite_item import PrerequisiteItemFactory
from program_management.business.group_element_years.detach import DetachEducationGroupYearStrategy
from program_management.business.group_element_years.management import CheckAuthorizedRelationshipDetach


class TestOptionDetachEducationGroupYearStrategy(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        cls.master_120 = TrainingFactory(education_group_type__name=TrainingType.PGRM_MASTER_120.name,
                                         academic_year=cls.academic_year)

        cls.option_in_parent = MiniTrainingFactory(
            acronym="OPT1",
            education_group_type__name=MiniTrainingType.OPTION.name,
            academic_year=cls.academic_year
        )
        cls.master_120_link_option = GroupElementYearFactory(parent=cls.master_120, child_branch=cls.option_in_parent)

        # Create finality structure
        cls.finality_group = GroupFactory(education_group_type__name=GroupType.FINALITY_120_LIST_CHOICE.name,
                                          academic_year=cls.academic_year)
        GroupElementYearFactory(parent=cls.master_120, child_branch=cls.finality_group)

        cls.master_120_specialized = GroupFactory(education_group_type__name=TrainingType.MASTER_MS_120.name,
                                                  academic_year=cls.academic_year)
        GroupElementYearFactory(parent=cls.finality_group, child_branch=cls.master_120_specialized)

    def setUp(self):
        self.mock_authorized_relationship_check_is_valid = mock.patch.object(
            CheckAuthorizedRelationshipDetach,
            "is_valid"
        )
        self.mock_authorized_relationship_check_is_valid.return_value = True
        self.mocked_perm = self.mock_authorized_relationship_check_is_valid.start()
        self.addCleanup(self.mock_authorized_relationship_check_is_valid.stop)

    def test_is_valid_case_detach_option_which_are_not_within_finality_master_120(self):
        """
        In this test, we ensure that we can detach an option at 2m because it is not present in any finality 2m
        """
        strategy = DetachEducationGroupYearStrategy(link=self.master_120_link_option)
        self.assertTrue(strategy.is_valid())

    def test_is_valid_case_detach_groups_which_contains_options_which_are_not_within_master_120(self):
        """
        In this test, we ensure that we can detach a groups which contains options at 2m because
        this options are present in any finality of this 2m
        """
        subgroup = GroupFactory(education_group_type__name=GroupType.SUB_GROUP.name,
                                academic_year=self.academic_year)
        master_120_link_subgroup = GroupElementYearFactory(parent=self.master_120, child_branch=subgroup)
        GroupElementYearFactory(parent=subgroup, child_branch=self.option_in_parent)

        strategy = DetachEducationGroupYearStrategy(link=master_120_link_subgroup)
        self.assertTrue(strategy.is_valid())

    def test_is_valid_case_detach_option_which_are_within_finality_master_120_but_present_more_time_in_2m(self):
        """
        In this test, we ensure that we can detach an option at 2m level because it is present two time in 2m and
        it is present in one finality of this 2m but, we will detach only one link in 2m
        """
        subgroup = GroupFactory(education_group_type__name=GroupType.SUB_GROUP.name,
                                academic_year=self.academic_year)
        master_120_link_subgroup = GroupElementYearFactory(parent=self.master_120, child_branch=subgroup)
        GroupElementYearFactory(parent=subgroup, child_branch=self.option_in_parent)

        GroupElementYearFactory(parent=self.master_120_specialized, child_branch=self.option_in_parent)
        strategy = DetachEducationGroupYearStrategy(link=master_120_link_subgroup)
        self.assertTrue(strategy.is_valid())

    def test_is_not_valid_case_detach_option_which_are_within_finality_master_120(self):
        """
        In this test, we ensure that we CANNOT detach an option at 2m level because
        it is present in one finality of this 2m
        """
        option = MiniTrainingFactory(education_group_type__name=MiniTrainingType.OPTION.name,
                                     academic_year=self.academic_year)
        GroupElementYearFactory(parent=self.master_120_specialized, child_branch=option)
        master_120_link_option = GroupElementYearFactory(
            parent=self.master_120,
            child_branch=option,
        )

        strategy = DetachEducationGroupYearStrategy(link=master_120_link_option)
        self.assertFalse(strategy.is_valid())

    def test_is_not_valid_case_detach_group_which_contains_option_which_are_within_finality_master_120(self):
        """
        In this test, we ensure that we CANNOT detach a group which contains options at 2m level because
        this options are present in one finality of this 2m
        """
        subgroup = GroupFactory(education_group_type__name=GroupType.SUB_GROUP.name,
                                academic_year=self.academic_year)
        GroupElementYearFactory(parent=self.master_120_specialized, child_branch=subgroup)
        option = MiniTrainingFactory(education_group_type__name=MiniTrainingType.OPTION.name,
                                     academic_year=self.academic_year)
        GroupElementYearFactory(parent=subgroup, child_branch=option)

        master_120_link_option = GroupElementYearFactory(parent=self.master_120, child_branch=option)

        strategy = DetachEducationGroupYearStrategy(link=master_120_link_option)
        self.assertFalse(strategy.is_valid())

    def test_is_not_valid_case_detach_group_which_contains_option_which_are_reused_in_multiple_2M(self):
        """
        In this test, we ensure that we CANNOT detach a group which are reused in two 2m because, one of
        those 2m structure will not be valid anymore
        """
        # Create first 2M
        #   2M
        #   |--OPT1
        #   |--GROUP1
        #      |--OPT1
        #   |--FINALITY_LIST
        #      |--2MS
        #         |--OPT1
        subgroup = GroupFactory(acronym='GROUP1', education_group_type__name=GroupType.SUB_GROUP.name,
                                academic_year=self.academic_year)
        GroupElementYearFactory(parent=self.master_120, child_branch=subgroup)
        group1_link_opt1 = GroupElementYearFactory(parent=subgroup, child_branch=self.option_in_parent)
        GroupElementYearFactory(parent=self.master_120_specialized, child_branch=self.option_in_parent)

        # Create another 2M
        #   2M
        #   |--GROUP1
        #      |--OPT1
        #   |--FINALITY_LIST
        #      |--2MD
        #         |--OPT1
        another_master_120 = TrainingFactory(education_group_type__name=TrainingType.PGRM_MASTER_120.name,
                                             academic_year=self.academic_year)
        GroupElementYearFactory(parent=another_master_120, child_branch=subgroup)
        another_finality_group = GroupFactory(education_group_type__name=GroupType.FINALITY_120_LIST_CHOICE.name,
                                              academic_year=self.academic_year)
        GroupElementYearFactory(parent=another_master_120, child_branch=another_finality_group)
        another_master_120_didactic = GroupFactory(education_group_type__name=TrainingType.MASTER_MD_120.name,
                                                   academic_year=self.academic_year)
        GroupElementYearFactory(parent=another_finality_group, child_branch=another_master_120_didactic)
        GroupElementYearFactory(parent=another_master_120_didactic, child_branch=self.option_in_parent)

        # We try to detach OPT1 from GROUP1 but it is not allowed because another 2M structure won't be valid anymore
        strategy = DetachEducationGroupYearStrategy(link=group1_link_opt1)
        self.assertFalse(strategy.is_valid())


class TestDetachPrerequisiteCheck(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.root = TrainingFactory(
            academic_year__current=True,
            education_group_type=EducationGroupTypeFactory(name=education_group_types.TrainingType.MASTER_MA_120.name)
        )
        cls.children_level_0 = GroupElementYearFactory.create_batch(
            1,
            parent=cls.root,
            child_branch__education_group_type__group=True,
            child_branch__academic_year=cls.root.academic_year
        )

        cls.children_level_1 = GroupElementYearFactory.create_batch(
            3,
            parent=cls.children_level_0[0].child_branch,
            child_branch__education_group_type__group=True,
            child_branch__academic_year=cls.root.academic_year
        )
        cls.children_level_2 = GroupElementYearFactory.create_batch(
            1,
            parent=cls.children_level_1[0].child_branch,
            child_branch__education_group_type__group=True,
            child_branch__academic_year=cls.root.academic_year
        )
        cls.lu_children_level_2 = GroupElementYearChildLeafFactory.create_batch(
            2,
            parent=cls.children_level_1[1].child_branch,
            child_leaf__academic_year=cls.root.academic_year
        )

        cls.lu_children_level_3 = GroupElementYearChildLeafFactory.create_batch(
            2,
            parent=cls.children_level_2[0].child_branch,
            child_leaf__academic_year=cls.root.academic_year
        )

    def setUp(self):
        self.mock_authorized_relationship_check_is_valid = mock.patch.object(
            CheckAuthorizedRelationshipDetach,
            "is_valid"
        )
        self.mock_authorized_relationship_check_is_valid.return_value = True
        self.mocked_perm = self.mock_authorized_relationship_check_is_valid.start()
        self.addCleanup(self.mock_authorized_relationship_check_is_valid.stop)

        self.prerequisite = PrerequisiteFactory(
            learning_unit_year=self.lu_children_level_3[0].child_leaf,
            education_group_year=self.root,
        )
        self.prerequisite_item = PrerequisiteItemFactory(
            prerequisite=self.prerequisite,
            learning_unit=self.lu_children_level_2[0].child_leaf.learning_unit
        )

    def test_when_no_prerequisite(self):
        strategy = DetachEducationGroupYearStrategy(self.children_level_1[2])
        self.assertIsNone(strategy._check_detach_prerequisite_rules())
        self.assertFalse(strategy.errors)
        self.assertFalse(strategy.warnings)

    def test_create_warnings_when_has_prerequisite_in_formation(self):
        strategy = DetachEducationGroupYearStrategy(self.children_level_2[0])
        strategy._check_detach_prerequisite_rules()
        self.assertFalse(strategy.errors)
        self.assertTrue(strategy.warnings)

    def test_create_error_when_is_prerequisite_in_formation(self):
        strategy = DetachEducationGroupYearStrategy(self.children_level_1[1])
        strategy._check_detach_prerequisite_rules()
        self.assertTrue(strategy.errors)

    def test_can_detach_if_duplicate_luy(self):
        GroupElementYearChildLeafFactory(
            parent=self.children_level_1[0].child_branch,
            child_leaf=self.lu_children_level_2[0].child_leaf
        )
        strategy = DetachEducationGroupYearStrategy(self.children_level_1[1])
        self.assertIsNone(strategy._check_detach_prerequisite_rules())

    def test_warnings_when_prerequisites_in_group_that_is_detached(self):
        strategy = DetachEducationGroupYearStrategy(self.children_level_0[0])
        strategy._check_detach_prerequisite_rules()
        self.assertTrue(strategy.warnings)

        strategy.delete_prerequisites()
        self.assertFalse(Prerequisite.objects.filter(id=self.prerequisite.id))
