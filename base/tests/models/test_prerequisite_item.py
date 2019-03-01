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
##############################################################################
from django.db import IntegrityError
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

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
        self.prerequisite = PrerequisiteFactory()

    def test_get_prerequisite_string_representation_no_item(self):
        self.assertEqual(
            self.prerequisite.prerequisite_string,
            ""
        )

    def test_get_prerequisite_string_representation_2_groupq_2_items(self):
        self.prerequisite_items_group_1 = _build_group_of_prerequisite_items(
            prerequisite=self.prerequisite,
            group=1,
            positions=1
        )
        self.prerequisite_items_group_2 = _build_group_of_prerequisite_items(
            prerequisite=self.prerequisite,
            group=2,
            positions=1
        )

        self.assertEqual(
            self.prerequisite.prerequisite_string,
            "LDROI1111 {AND} LDROI1121".format(AND=_('AND'))
        )

    def test_get_prerequisite_string_representation_two_groups(self):
        self.prerequisite_items_group_1 = _build_group_of_prerequisite_items(
            prerequisite=self.prerequisite,
            group=1,
            positions=3
        )
        self.prerequisite_items_group_2 = _build_group_of_prerequisite_items(
            prerequisite=self.prerequisite,
            group=2,
            positions=3
        )

        self.assertEqual(
            self.prerequisite.prerequisite_string,
            "(LDROI1111 {OR} LDROI1112 {OR} LDROI1113) {AND} (LDROI1121 {OR} LDROI1122 {OR} LDROI1123)".format(
                OR=_('OR'),
                AND=_('AND')
            )
        )


def _build_group_of_prerequisite_items(prerequisite, group, positions):
    return [
        PrerequisiteItemFactory(
            prerequisite=prerequisite,
            learning_unit=LearningUnitYearFactory(acronym='LDROI11{}{}'.format(group, i)).learning_unit,
            group_number=group,
            position=i
        )
        for i in range(1, 1 + positions)
    ]
