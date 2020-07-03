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
import re

from django.test import TestCase

from base.business.education_groups.create import create_initial_group_element_year_structure, \
    _get_cnum_subdivision, _get_or_create_branch
from base.models.education_group import EducationGroup
from base.models.education_group_type import EducationGroupType
from base.models.education_group_year import EducationGroupYear
from base.models.enums import education_group_types, education_group_categories
from base.models.enums.education_group_types import GroupType
from base.models.group_element_year import GroupElementYear
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.education_group import EducationGroupFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.validation_rule import ValidationRuleFactory


class TestCreateInitialGroupElementYearStructure(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.master_type = EducationGroupTypeFactory(
            category=education_group_categories.TRAINING,
            name=education_group_types.TrainingType.MASTER_MA_120.name,
        )
        cls.finality_type = EducationGroupTypeFactory(
            category=education_group_categories.GROUP,
            name=education_group_types.GroupType.FINALITY_120_LIST_CHOICE.name,
            external_id="osis.education_group_type_finality120listchoice"
        )
        cls.major_type = EducationGroupTypeFactory(
            category=education_group_categories.GROUP,
            name=education_group_types.GroupType.MAJOR_LIST_CHOICE.name,
            external_id="osis.education_group_type_majorlistchoice"
        )

        cls.current_academic_year = create_current_academic_year()
        cls.next_academic_year = AcademicYearFactory(year=cls.current_academic_year.year + 1)

        cls.auth_rel = AuthorizedRelationshipFactory(
            parent_type=cls.master_type,
            child_type=cls.finality_type,
            min_count_authorized=1,
        )
        cls.validation_rule_title = ValidationRuleFactory(
            field_reference="base_educationgroupyear.title.osis.education_group_type_finality120listchoice",
            initial_value="Liste au choix de Finalités",
        )
        cls.validation_rule_partial_acronym = ValidationRuleFactory(
            field_reference="base_educationgroupyear.partial_acronym.osis.education_group_type_finality120listchoice",
            initial_value="400G",
        )

        cls.validation_rule_title_major = ValidationRuleFactory(
            field_reference="base_educationgroupyear.title.osis.education_group_type_majorlistchoice",
            initial_value="Majeure",
        )
        cls.validation_rule_partial_acronym_major = ValidationRuleFactory(
            field_reference="base_educationgroupyear.partial_acronym.osis.education_group_type_majorlistchoice",
            initial_value="200K",
        )

    def setUp(self):
        self.egy = EducationGroupYearFactory(
            education_group_type=self.master_type,
            acronym="TEST2M",
            partial_acronym="LTEST100B",
            academic_year=self.current_academic_year
        )
        self.egy_next_year = EducationGroupYearFactory(
            education_group_type=self.master_type,
            acronym="TEST2M",
            partial_acronym="LTEST100B",
            academic_year=self.next_academic_year,
            education_group=self.egy.education_group
        )

    def test_should_return_empty_result_when_no_education_group_years_parent(self):
        children = create_initial_group_element_year_structure([])
        self.assertDictEqual(
            children,
            {}
        )

    def test_education_group_year_children_attribute(self):
        attributes_to_inherit = ("academic_year", "main_teaching_campus", "management_entity")
        expected_title = "{} {}".format(self.validation_rule_title.initial_value, self.egy.acronym)
        expected_acronym = "{}{}".format(
            self.validation_rule_title.initial_value.replace(" ", "").upper(),
            self.egy.acronym
        )

        child_egy = create_initial_group_element_year_structure([self.egy])[self.egy.id][0].child_branch

        for field in attributes_to_inherit:
            self.assertEqual(getattr(child_egy, field), getattr(self.egy, field))
        self.assertEqual(child_egy.education_group_type, self.finality_type)
        self.assertEqual(child_egy.title, expected_title)
        self.assertEqual(child_egy.partial_acronym, "LTEST400G")
        self.assertEqual(child_egy.acronym, expected_acronym)
        self.assertTrue(child_egy.id)

    def test_should_truncate_acronym_when_surpassing_limit_fixed_by_acronym_field(self):
        self.egy.acronym = "THIS iS WAY TOO BIG FOR AN ACRONYM HAHA"
        self.egy.save()

        child_egy = create_initial_group_element_year_structure([self.egy])[self.egy.id][0].child_branch
        expected_acronym = "{}{}".format(
            self.validation_rule_title.initial_value.replace(" ", "").upper(),
            self.egy.acronym
        )[:EducationGroupYear._meta.get_field("acronym").max_length]
        self.assertEqual(child_egy.acronym, expected_acronym)

    def test_education_group_year_children_attribute_empty_partial_acronym(self):
        """ Check if the app can handle an empty partial acronym
        TODO : Remove that test when the db will be cleaned.
        """
        attributes_to_inherit = ("academic_year", "main_teaching_campus", "management_entity")
        expected_title = "{} {}".format(self.validation_rule_title.initial_value, self.egy.acronym)
        expected_acronym = "{}{}".format(
            self.validation_rule_title.initial_value.replace(" ", "").upper(),
            self.egy.acronym
        )

        self.egy.partial_acronym = None

        child_egy = create_initial_group_element_year_structure([self.egy])[self.egy.id][0].child_branch

        for field in attributes_to_inherit:
            self.assertEqual(getattr(child_egy, field), getattr(self.egy, field))
        self.assertEqual(child_egy.education_group_type, self.finality_type)
        self.assertEqual(child_egy.title, expected_title)
        self.assertEqual(child_egy.partial_acronym, "")
        self.assertEqual(child_egy.acronym, expected_acronym)
        self.assertTrue(child_egy.id)

    def test_should_create_education_group_with_start_and_year_equal_to_parent_academic_year(self):
        child_egy = create_initial_group_element_year_structure([self.egy])[self.egy.id][0].child_branch
        self.assertEqual(
            child_egy.education_group.start_year,
            self.egy.academic_year
        )
        self.assertEqual(
            child_egy.education_group.end_year,
            self.egy.academic_year
        )

    def test_should_increment_cnum_of_child_partial_acronym_to_avoid_conflicted_acronyms(self):
        EducationGroupYearFactory(partial_acronym="LTEST400G")
        EducationGroupYearFactory(partial_acronym="LTEST401G")
        child_egy = create_initial_group_element_year_structure([self.egy])[self.egy.id][0].child_branch
        self.assertEqual(
            child_egy.partial_acronym,
            "LTEST402G"
        )

    def test_should_create_group_element_year_if_not_existing(self):
        self.assertFalse(GroupElementYear.objects.filter(parent=self.egy).exists())
        edy_type = EducationGroupType.objects.get(name=GroupType.FINALITY_120_LIST_CHOICE.name)
        _get_or_create_branch(edy_type, "TITLE", "PARTIAL", self.egy)
        child_edy = EducationGroupYear.objects.get(
            education_group__start_year=self.egy.academic_year,
            education_group__end_year=self.egy.academic_year
        )
        self.assertTrue(GroupElementYear.objects.filter(parent=self.egy, child_branch=child_edy).exists())

    def test_should_not_create_group_element_year_if_existing(self):
        edy_type = EducationGroupType.objects.get(name=GroupType.FINALITY_120_LIST_CHOICE.name)
        ed = EducationGroup.objects.create(
            start_year=self.egy.academic_year,
            end_year=self.egy.academic_year
        )
        child_egy = EducationGroupYear.objects.create(
            academic_year=self.egy.academic_year,
            education_group=ed,
            education_group_type=edy_type
        )
        GroupElementYear.objects.create(parent=self.egy, child_branch=child_egy)
        self.assertEqual(GroupElementYear.objects.filter(parent=self.egy, child_branch=child_egy).count(), 1)
        _get_or_create_branch(edy_type, "TITLE", "PARTIAL", self.egy)
        self.assertEqual(GroupElementYear.objects.filter(parent=self.egy, child_branch=child_egy).count(), 1)

    def test_should_create_education_group_if_not_existing(self):
        acronym = "{child_title}{parent_acronym}".format(
            child_title="TITLE",
            parent_acronym=self.egy.acronym
        )
        self.assertFalse(EducationGroup.objects.filter(educationgroupyear__acronym=acronym).exists())
        edy_type = EducationGroupType.objects.get(name=GroupType.FINALITY_120_LIST_CHOICE.name)
        _get_or_create_branch(edy_type, "TITLE", "PARTIAL", self.egy)
        self.assertTrue(EducationGroup.objects.filter(educationgroupyear__acronym=acronym).exists())

    def test_should_not_create_education_group_if_existing(self):
        acronym = "{child_title}{parent_acronym}".format(
            child_title="TITLE",
            parent_acronym=self.egy.acronym
        )
        EducationGroupYearFactory(
            acronym=acronym,
            education_group=EducationGroupFactory(
                start_year=self.egy.academic_year,
                end_year=self.egy.academic_year
            )
        )
        self.assertEqual(EducationGroup.objects.filter(educationgroupyear__acronym=acronym).count(), 1)
        edy_type = EducationGroupType.objects.get(name=GroupType.FINALITY_120_LIST_CHOICE.name)
        _get_or_create_branch(edy_type, "TITLE", "PARTIAL", self.egy)
        self.assertEqual(EducationGroup.objects.filter(educationgroupyear__acronym=acronym).distinct().count(), 1)

    def test_should_create_children_for_education_group_year_equal_to_number_of_authorized_relationships(self):
        AuthorizedRelationshipFactory(
            parent_type=self.master_type,
            child_type=self.major_type,
            min_count_authorized=1,
        )
        children_egy = create_initial_group_element_year_structure([self.egy])[self.egy.id]
        self.assertEqual(len(children_egy), 2)

    def test_should_create_children_for_each_education_group_year(self):
        children_egys = create_initial_group_element_year_structure([self.egy, self.egy_next_year])
        self.assertEqual(len(children_egys), 2)
        self.assertEqual(len(children_egys[self.egy.id]), 1)
        self.assertEqual(len(children_egys[self.egy_next_year.id]), 1)

    def test_should_keep_partial_acronym_between_years(self):
        children_egys = create_initial_group_element_year_structure([self.egy, self.egy_next_year])
        partial_acronym = children_egys[self.egy.id][0].child_branch.partial_acronym
        partial_acronym_next_year = children_egys[self.egy_next_year.id][0].child_branch.partial_acronym
        self.assertTrue(
            partial_acronym == partial_acronym_next_year == "LTEST400G"
        )

    def test_should_reuse_past_partial_acronym(self):
        previous_academic_year = AcademicYearFactory(year=self.egy.academic_year.year - 1)
        previous_egy = EducationGroupYearFactory(
            education_group_type=self.master_type,
            acronym="TEST2M",
            partial_acronym="LTEST100B",
            academic_year=previous_academic_year,
            education_group=self.egy.education_group,
        )
        previous_child = EducationGroupYearFactory(
            education_group_type=self.finality_type,
            partial_acronym="LTEST503G",
            academic_year=previous_academic_year,
        )
        GroupElementYearFactory(
            parent=previous_egy,
            child_branch=previous_child
        )
        children_egys = create_initial_group_element_year_structure([self.egy])

        self.assertEqual(
            previous_child.partial_acronym,
            children_egys[self.egy.id][0].child_branch.partial_acronym
        )

        self.assertEqual(
            previous_child.education_group,
            children_egys[self.egy.id][0].child_branch.education_group
        )

    def test_should_not_recreate_existing_children(self):
        child = EducationGroupYearFactory(
            education_group_type=self.finality_type,
            partial_acronym="LTEST503G",
            academic_year=self.egy.academic_year,
        )
        grp_ele = GroupElementYearFactory(
            parent=self.egy,
            child_branch=child
        )
        children_egys = create_initial_group_element_year_structure([self.egy])
        self.assertEqual(
            grp_ele.id,
            children_egys[self.egy.id][0].id
        )

    def test_should_copy_data_from_previous_year(self):
        previous_academic_year = AcademicYearFactory(year=self.egy.academic_year.year - 1)
        previous_egy = EducationGroupYearFactory(
            education_group_type=self.master_type,
            acronym="TEST2M",
            partial_acronym="LTEST100B",
            academic_year=previous_academic_year,
            education_group=self.egy.education_group,
        )
        previous_child = EducationGroupYearFactory(
            education_group_type=self.finality_type,
            partial_acronym="LTEST503G",
            academic_year=previous_academic_year,
        )
        GroupElementYearFactory(
            parent=previous_egy,
            child_branch=previous_child
        )

        current_child = EducationGroupYearFactory(
            education_group_type=self.finality_type,
            partial_acronym="LTEST504G",
            academic_year=self.current_academic_year,
        )
        GroupElementYearFactory(
            parent=self.egy,
            child_branch=current_child
        )
        children_egys = create_initial_group_element_year_structure([previous_egy, self.egy, self.egy_next_year])

        self.assertEqual(
            current_child.partial_acronym,
            children_egys[self.egy_next_year.id][0].child_branch.partial_acronym
        )

    def test_get_cnum_subdivision(self):
        cnum, subdivision = _get_cnum_subdivision("100T", re.compile('^(?P<cnum>\\d{3})(?P<subdivision>[A-Z])$'))
        self.assertEqual(cnum, "100")
        self.assertEqual(subdivision, "T")

    def test_no_cnum_subdivision(self):
        cnum, subdivision = _get_cnum_subdivision("", re.compile('^(?P<cnum>\\d{3})(?P<subdivision>[A-Z])$'))
        self.assertIsNone(cnum)
        self.assertIsNone(subdivision)

        cnum, subdivision = _get_cnum_subdivision("100", re.compile('^(?P<cnum>\\d{3})(?P<subdivision>[A-Z])$'))
        self.assertIsNone(cnum)
        self.assertIsNone(subdivision)

        cnum, subdivision = _get_cnum_subdivision("T", re.compile('^(?P<cnum>\\d{3})(?P<subdivision>[A-Z])$'))
        self.assertIsNone(cnum)
        self.assertIsNone(subdivision)
