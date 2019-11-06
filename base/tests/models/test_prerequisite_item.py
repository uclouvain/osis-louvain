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
from django.db import IntegrityError
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.prerequisite import PrerequisiteFactory
from base.tests.factories.prerequisite_item import PrerequisiteItemFactory


class TestPrerequisiteItem(TestCase):
    def setUp(self):
        self.learning_unit_is_prerequisite = LearningUnitFactory()
        self.learning_unit_not_prerequisite = LearningUnitFactory()
        self.learning_unit_year_with_prerequisite = LearningUnitYearFactory()
        self.learning_unit_year_without_prerequisite = LearningUnitYearFactory()
        self.prerequisite = PrerequisiteFactory(learning_unit_year=self.learning_unit_year_with_prerequisite)
        self.prerequisite_item = PrerequisiteItemFactory(
            prerequisite=self.prerequisite,
            learning_unit=self.learning_unit_is_prerequisite
        )

    def test_find_by_prerequisite(self):
        self.assertEqual(
            list(self.prerequisite.prerequisiteitem_set.all()),
            [self.prerequisite_item]
        )

    def test_learning_unit_prerequisite_to_itself_forbidden(self):
        with self.assertRaisesMessage(IntegrityError, "A learning unit cannot be prerequisite to itself"):
            PrerequisiteItemFactory(
                prerequisite=self.prerequisite,
                learning_unit=self.learning_unit_year_with_prerequisite.learning_unit
            )


class TestPrerequisiteString(TestCase):
    def setUp(self):
        academic_year = create_current_academic_year()
        luy_prerequisite = LearningUnitYearFactory(acronym='LDROI1223', academic_year=academic_year)
        self.prerequisite = PrerequisiteFactory(learning_unit_year=luy_prerequisite)

        self.luy_prerequisite_item_1_1 = LearningUnitYearFactory(acronym='LDROI1001', academic_year=academic_year)
        self.luy_prerequisite_item_1_2 = LearningUnitYearFactory(acronym='LDROI1002', academic_year=academic_year)
        self.luy_prerequisite_item_1_3 = LearningUnitYearFactory(acronym='LDROI1003', academic_year=academic_year)

        self.luy_prerequisite_item_2_1 = LearningUnitYearFactory(acronym='LDROI2001', academic_year=academic_year)
        self.luy_prerequisite_item_2_2 = LearningUnitYearFactory(acronym='LDROI2002', academic_year=academic_year)
        self.luy_prerequisite_item_2_3 = LearningUnitYearFactory(acronym='LDROI2003', academic_year=academic_year)

    def test_get_prerequisite_string_representation_no_item(self):
        self.assertEqual(
            self.prerequisite.prerequisite_string,
            ""
        )

    def test_get_prerequisite_string_representation_2_groupq_2_items(self):
        PrerequisiteItemFactory(
            prerequisite=self.prerequisite,
            learning_unit=self.luy_prerequisite_item_1_1.learning_unit,
            group_number=1,
            position=1
        )

        PrerequisiteItemFactory(
            prerequisite=self.prerequisite,
            learning_unit=self.luy_prerequisite_item_2_1.learning_unit,
            group_number=2,
            position=1
        )

        expected_string = "{} {} {}".format(
            self.luy_prerequisite_item_1_1.acronym,
            _('AND'),
            self.luy_prerequisite_item_2_1.acronym
        )

        self.assertEqual(
            self.prerequisite.prerequisite_string,
            expected_string
        )

    def test_get_prerequisite_string_representation_two_groups(self):
        PrerequisiteItemFactory(
            prerequisite=self.prerequisite,
            learning_unit=self.luy_prerequisite_item_1_1.learning_unit,
            group_number=1,
            position=1
        )
        PrerequisiteItemFactory(
            prerequisite=self.prerequisite,
            learning_unit=self.luy_prerequisite_item_1_2.learning_unit,
            group_number=1,
            position=2
        )
        PrerequisiteItemFactory(
            prerequisite=self.prerequisite,
            learning_unit=self.luy_prerequisite_item_1_3.learning_unit,
            group_number=1,
            position=3
        )

        PrerequisiteItemFactory(
            prerequisite=self.prerequisite,
            learning_unit=self.luy_prerequisite_item_2_1.learning_unit,
            group_number=2,
            position=1
        )
        PrerequisiteItemFactory(
            prerequisite=self.prerequisite,
            learning_unit=self.luy_prerequisite_item_2_2.learning_unit,
            group_number=2,
            position=2
        )
        PrerequisiteItemFactory(
            prerequisite=self.prerequisite,
            learning_unit=self.luy_prerequisite_item_2_3.learning_unit,
            group_number=2,
            position=3
        )


        expected = \
            "(%s %s %s %s " \
            "%s) %s (%s %s " \
            "%s %s %s)" % (
                self.luy_prerequisite_item_1_1.acronym,
                _('OR'),
                self.luy_prerequisite_item_1_2.acronym,
                _('OR'),
                self.luy_prerequisite_item_1_3.acronym,
                _('AND'),
                self.luy_prerequisite_item_2_1.acronym,
                _('OR'),
                self.luy_prerequisite_item_2_2.acronym,
                _('OR'),
                self.luy_prerequisite_item_2_3.acronym
            )
        self.assertEqual(
            self.prerequisite.prerequisite_string,
            expected
        )
