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
#############################################################################
import itertools

from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from base.models.enums.prerequisite_operator import AND, OR
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import TrainingFactory, MiniTrainingFactory, EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory, LearningUnitYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.prerequisite import PrerequisiteFactory
from base.tests.factories.prerequisite_item import PrerequisiteItemFactory
from base.tests.factories.user import UserFactory
from program_management.business.learning_units import prerequisite
from program_management.views.generic import NO_PREREQUISITES


class TestLearningUnitsAcronymsFromPrerequisite(TestCase):
    def setUp(self):
        self.prerequisite = PrerequisiteFactory()

    def test_empty_prerequisite_should_return_empty_list(self):
        self.assertEqual(prerequisite.extract_learning_units_acronym_from_prerequisite(self.prerequisite),
                         [])

    def test_when_prerequisite_consits_of_one_learning_unit(self):
        learning_unit_year = LearningUnitYearFactory(acronym="LSINF1121")
        PrerequisiteItemFactory(
            learning_unit=learning_unit_year.learning_unit,
            prerequisite=self.prerequisite
        )

        self.assertEqual(
            prerequisite.extract_learning_units_acronym_from_prerequisite(self.prerequisite),
            ["LSINF1121"]
        )

    def test_when_prerequisites_multiple_learning_units_but_no_parentheses(self):
        learning_unit_year = LearningUnitYearFactory(acronym="LSINF1121")
        PrerequisiteItemFactory(
            learning_unit=learning_unit_year.learning_unit,
            prerequisite=self.prerequisite,
            group_number=1,
            position=1,
        )
        learning_unit_year = LearningUnitYearFactory(acronym="LBIR1245A")
        PrerequisiteItemFactory(
            learning_unit=learning_unit_year.learning_unit,
            prerequisite=self.prerequisite,
            group_number=2,
            position=1,
        )
        learning_unit_year = LearningUnitYearFactory(acronym="LDROI4578")
        PrerequisiteItemFactory(
            learning_unit=learning_unit_year.learning_unit,
            prerequisite=self.prerequisite,
            group_number=3,
            position=1,
        )

        self.prerequisite.main_operator = AND
        self.prerequisite.save()
        self.assertCountEqual(
            prerequisite.extract_learning_units_acronym_from_prerequisite(self.prerequisite),
            ["LSINF1121", "LBIR1245A", "LDROI4578"]
        )

        self.prerequisite.main_operator = OR
        self.prerequisite.save()
        self.assertCountEqual(
            prerequisite.extract_learning_units_acronym_from_prerequisite(self.prerequisite),
            ["LSINF1121", "LBIR1245A", "LDROI4578"]
        )

    def test_when_prerequisites_multiple_learning_units_with_parentheses(self):
        learning_unit_year = LearningUnitYearFactory(acronym="LSINF1121")
        PrerequisiteItemFactory(
            learning_unit=learning_unit_year.learning_unit,
            prerequisite=self.prerequisite,
            group_number=1,
            position=1,
        )
        learning_unit_year = LearningUnitYearFactory(acronym="LBIR1245A")
        PrerequisiteItemFactory(
            learning_unit=learning_unit_year.learning_unit,
            prerequisite=self.prerequisite,
            group_number=1,
            position=2,
        )
        learning_unit_year = LearningUnitYearFactory(acronym="LDROI4578")
        PrerequisiteItemFactory(
            learning_unit=learning_unit_year.learning_unit,
            prerequisite=self.prerequisite,
            group_number=2,
            position=1,
        )

        self.prerequisite.main_operator = AND
        self.prerequisite.save()
        self.assertCountEqual(
            prerequisite.extract_learning_units_acronym_from_prerequisite(self.prerequisite),
            ["LSINF1121", "LBIR1245A", "LDROI4578"]
        )

        self.prerequisite.main_operator = OR
        self.prerequisite.save()
        self.assertCountEqual(
            prerequisite.extract_learning_units_acronym_from_prerequisite(self.prerequisite),
            ["LSINF1121", "LBIR1245A", "LDROI4578"]
        )


class TestGetLearningUnitsWhichAreNotInsideTraining(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        cls.education_group_year_root = TrainingFactory(academic_year=cls.academic_year)
        cls.education_group_year_childs = [MiniTrainingFactory(academic_year=cls.academic_year) for _ in range(0, 3)]

        cls.group_element_years_root_to_child = [
            GroupElementYearFactory(parent=cls.education_group_year_root,
                                    child_leaf=None,
                                    child_branch=cls.education_group_year_childs[i])
            for i in range(0, len(cls.education_group_year_childs))
        ]

        cls.group_element_years_child_0 = [
            GroupElementYearFactory(parent=cls.education_group_year_childs[0],
                                    child_leaf=LearningUnitYearFakerFactory(
                                        learning_container_year__academic_year=cls.academic_year),
                                    child_branch=None)
            for i in range(0, 2)
        ]

        cls.group_element_years_child_2 = [
            GroupElementYearFactory(parent=cls.education_group_year_childs[2],
                                    child_leaf=LearningUnitYearFakerFactory(
                                        learning_container_year__academic_year=cls.academic_year),
                                    child_branch=None)
            for i in range(0, 4)
        ]

        cls.all_learning_units_acronym = [
            gey.child_leaf.acronym for gey in itertools.chain(cls.group_element_years_child_0,
                                                              cls.group_element_years_child_2)
        ]

    def test_empty_acronym_list_should_return_empty_list(self):
        self.assertEqual(
            prerequisite.get_learning_units_which_are_outside_of_education_group(self.education_group_year_root, []),
            []
        )

    def test_should_return_empty_list_when_all_learning_units_are_inside_education_group_year_root(self):
        self.assertEqual(
            prerequisite.get_learning_units_which_are_outside_of_education_group(self.education_group_year_root,
                                                                                 self.all_learning_units_acronym),
            []
        )

    def test_should_return_acronym_of_learnings_units_not_present_in_education_group_year(self):
        luy_outside = LearningUnitYearFakerFactory(learning_container_year__academic_year=self.academic_year)
        luy_outside_2 = LearningUnitYearFakerFactory(learning_container_year__academic_year=self.academic_year)
        learning_units_acronym = [luy_outside.acronym] + self.all_learning_units_acronym
        self.assertEqual(
            prerequisite.get_learning_units_which_are_outside_of_education_group(self.education_group_year_root,
                                                                                 learning_units_acronym),
            [luy_outside.acronym]
        )

        learning_units_acronym = [luy_outside.acronym, luy_outside_2.acronym] + self.all_learning_units_acronym
        self.assertCountEqual(
            prerequisite.get_learning_units_which_are_outside_of_education_group(self.education_group_year_root,
                                                                                 learning_units_acronym),
            [luy_outside.acronym, luy_outside_2.acronym]
        )


class TestShowPrerequisites(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = UserFactory()
        cls.person = PersonFactory(user=cls.user)
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))

    def setUp(self):
        self.client.force_login(self.user)

    def test_should_return_false_if_in_no_prerequisites(self):
        for egy_type in NO_PREREQUISITES:
            with self.subTest(egy_type=egy_type):
                egy = EducationGroupYearFactory(education_group_type__name=egy_type)
                lu = LearningUnitYearFactory()
                url = reverse("learning_unit_utilization", args=[egy.pk, lu.pk])
                response = self.client.get(url)
                self.assertFalse(response.context['show_prerequisites'])
