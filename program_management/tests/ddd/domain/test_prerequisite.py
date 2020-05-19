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
from django.test import SimpleTestCase
from django.utils.translation import gettext_lazy as _

from base.models.enums import prerequisite_operator
from program_management.ddd.domain import prerequisite
from program_management.ddd.domain.prerequisite import NullPrerequisite
from program_management.tests.ddd.factories.node import NodeLearningUnitYearFactory
from program_management.tests.ddd.factories.prerequisite import PrerequisiteItemFactory, PrerequisiteFactory, \
    PrerequisiteItemGroupFactory


class TestPrerequisiteItem(SimpleTestCase):
    def test_case_assert_str_method(self):
        p_item = prerequisite.PrerequisiteItem(code='LDROI1200', year=2018)
        expected_str = p_item.code

        self.assertEqual(str(p_item), expected_str)

    def test_eq_when_code_and_year_are_the_same(self):
        item1 = PrerequisiteItemFactory(code='code', year=2018)
        item2 = PrerequisiteItemFactory(code='code', year=2018)
        self.assertEqual(item1, item2)

    def test_eq_when_code_is_different(self):
        item1 = PrerequisiteItemFactory(code='code', year=2018)
        item2 = PrerequisiteItemFactory(code='code2', year=2018)
        self.assertNotEqual(item1, item2)

    def test_eq_when_year_is_different(self):
        item1 = PrerequisiteItemFactory(code='code', year=2018)
        item2 = PrerequisiteItemFactory(code='code', year=2019)
        self.assertNotEqual(item1, item2)


class TestPrerequisiteGroupItem(SimpleTestCase):
    def test_case_assert_invalid_operator_raise_exception(self):
        with self.assertRaises(AssertionError):
            prerequisite.PrerequisiteItemGroup(operator="XOR")

    def test_case_assert_str_method_no_element_on_group(self):
        p_group = prerequisite.PrerequisiteItemGroup(operator=prerequisite_operator.OR)
        self.assertEqual(str(p_group), '')

    def test_case_assert_str_method_one_element_on_group(self):
        p_group = prerequisite.PrerequisiteItemGroup(operator=prerequisite_operator.OR)
        p_group.add_prerequisite_item('LDROI1200', 2018)

        expected_str = 'LDROI1200'
        self.assertEqual(str(p_group), expected_str)

    def test_case_assert_str_method_multiple_elements_on_group(self):
        p_group = prerequisite.PrerequisiteItemGroup(operator=prerequisite_operator.OR)
        p_group.add_prerequisite_item('LDROI1200', 2018)
        p_group.add_prerequisite_item('LAGRO2200', 2018)

        expected_str = 'LDROI1200 {OR} LAGRO2200'.format(OR=_(prerequisite_operator.OR))
        self.assertEqual(str(p_group), expected_str)


class TestPrerequisite(SimpleTestCase):
    def setUp(self):
        self.p_group = prerequisite.PrerequisiteItemGroup(operator=prerequisite_operator.OR)
        self.p_group.add_prerequisite_item('LDROI1300', 2018)
        self.p_group.add_prerequisite_item('LAGRO2400', 2018)

        self.p_group_2 = prerequisite.PrerequisiteItemGroup(operator=prerequisite_operator.OR)
        self.p_group_2.add_prerequisite_item('LDROI1400', 2018)

    def test_case_assert_invalid_main_operator_raise_exception(self):
        with self.assertRaises(AssertionError):
            prerequisite.Prerequisite(main_operator="XOR")

    def test_case_assert_str_method_no_group(self):
        p_req = prerequisite.Prerequisite(main_operator=prerequisite_operator.AND)
        self.assertEqual(str(p_req), '')

    def test_case_assert_str_method_with_one_group(self):
        p_req = prerequisite.Prerequisite(main_operator=prerequisite_operator.AND)
        p_req.add_prerequisite_item_group(self.p_group)

        expected_str = 'LDROI1300 {OR} LAGRO2400'.format(OR=_(prerequisite_operator.OR))
        self.assertEqual(str(p_req), expected_str)

    def test_case_assert_str_method_with_multiple_groups(self):
        p_req = prerequisite.Prerequisite(main_operator=prerequisite_operator.AND)
        p_req.add_prerequisite_item_group(self.p_group)
        p_req.add_prerequisite_item_group(self.p_group_2)

        expected_str = '(LDROI1300 {OR} LAGRO2400) {AND} LDROI1400'.format(
            OR=_(prerequisite_operator.OR),
            AND=_(prerequisite_operator.AND)
        )
        self.assertEqual(str(p_req), expected_str)


class TestRemovePrerequisiteItem(SimpleTestCase):

    def test_when_prerequisite_item_groups_is_empty(self):
        prerequisite = PrerequisiteFactory(prerequisite_item_groups=[])
        self.assertIsNone(prerequisite.remove_prerequisite_item('code', 2018))
        self.assertListEqual(prerequisite.get_all_prerequisite_items(), [])
        self.assertFalse(prerequisite.has_changed)

    def test_when_item_to_remove_does_not_exist(self):
        existing_item = PrerequisiteItemFactory()
        prerequisite = PrerequisiteFactory(
            prerequisite_item_groups=[
                PrerequisiteItemGroupFactory(
                    prerequisite_items=[existing_item]
                ),
            ]
        )
        inexisting_year = 99999
        self.assertIsNone(prerequisite.remove_prerequisite_item("Inexisting code", inexisting_year))
        self.assertListEqual(prerequisite.get_all_prerequisite_items(), [existing_item])
        self.assertFalse(prerequisite.has_changed)

    def test_when_item_to_remove_exist(self):
        existing_item = PrerequisiteItemFactory()
        prerequisite = PrerequisiteFactory(
            prerequisite_item_groups=[
                PrerequisiteItemGroupFactory(
                    prerequisite_items=[existing_item]
                ),
            ]
        )
        self.assertIsNone(prerequisite.remove_prerequisite_item(existing_item.code, existing_item.year))
        self.assertListEqual(prerequisite.get_all_prerequisite_items(), list())
        self.assertTrue(prerequisite.has_changed)


class TestgetAllPrerequisiteItems(SimpleTestCase):

    def test_when_prerequisite_item_groups_is_empty(self):
        prerequisite = PrerequisiteFactory(prerequisite_item_groups=[])
        self.assertListEqual(prerequisite.get_all_prerequisite_items(), [])

    def test_when_contains_1_item(self):
        item = PrerequisiteItemFactory()
        prerequisite = PrerequisiteFactory(
            prerequisite_item_groups=[
                PrerequisiteItemGroupFactory(
                    prerequisite_items=[item]
                ),
            ]
        )
        expected_result = [item]
        self.assertListEqual(prerequisite.get_all_prerequisite_items(), expected_result)

    def test_when_contains_multiple_items_in_multiple_item_groups(self):
        item = PrerequisiteItemFactory()
        item2 = PrerequisiteItemFactory()
        item3 = PrerequisiteItemFactory()
        item4 = PrerequisiteItemFactory()
        prerequisite = PrerequisiteFactory(
            prerequisite_item_groups=[
                PrerequisiteItemGroupFactory(
                    prerequisite_items=[item, item2]
                ),
                PrerequisiteItemGroupFactory(
                    prerequisite_items=[item3]
                ),
                PrerequisiteItemGroupFactory(
                    prerequisite_items=[item4]
                ),
            ]
        )
        expected_result = [item, item2, item3, item4]
        self.assertListEqual(prerequisite.get_all_prerequisite_items(), expected_result)


class TestConstructPrerequisiteFromExpression(SimpleTestCase):
    def test_return_null_prerequisite_when_empty_expression_given(self):
        self.assertIsInstance(
            prerequisite.factory.from_expression("", 2019),
            NullPrerequisite
        )

    def test_return_prerequisite_object_when_expression_given(self):
        prerequisite_expression = "LOSIS4525 OU (LMARC5823 ET BRABD6985)"

        prerequisite_obj = prerequisite.factory.from_expression(prerequisite_expression, 2019)
        self.assertEqual(
            prerequisite_expression,
            str(prerequisite_obj)
        )
