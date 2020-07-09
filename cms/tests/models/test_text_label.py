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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.core.exceptions import ValidationError
from django.test import TestCase

from cms.models import text_label
from cms.models.text_label import TextLabel
from cms.tests.factories.text_label import TextLabelFactory
from osis_common.utils.models import get_object_or_none


class TextLabelTest(TestCase):
    def test_with_order_negative(self):
        text_label = TextLabelFactory.build(order=-10)
        with self.assertRaises(ValidationError):
            text_label.full_clean()
            text_label.save()

    def test_without_parent_and_empty_database(self):
        text_label = TextLabelFactory(order=10)
        self.assertEqual(text_label.order, 1)

    def test_without_parent_one_same_tree_level(self):
        TextLabelFactory(order=1)  # Order: 1
        tl_order_2 = TextLabelFactory(order=10)
        self.assertEqual(tl_order_2.order, 2)

    def test_without_parent_one_same_tree_level_shift_value(self):
        tl_initial_1 = TextLabelFactory(order=1)  # Order: 1
        tl_initial_2 = TextLabelFactory(order=2)  # Order: 2
        tl_new_1 = TextLabelFactory(order=1)  # Order: 1
        tl_initial_1.refresh_from_db()
        tl_initial_2.refresh_from_db()
        self.assertEqual(tl_new_1.order, 1)
        self.assertEqual(tl_initial_1.order, 2)
        self.assertEqual(tl_initial_2.order, 3)

    def test_with_one_parent_and_empty_leaf(self):
        parent = TextLabelFactory(order=1)
        tl_child = TextLabelFactory(parent=parent, order=10)
        self.assertEqual(parent.order, 1)
        self.assertEqual(tl_child.order, 1)

    def test_with_one_parent_one_same_tree_level(self):
        parent = TextLabelFactory(order=1)
        tl_child_1 = TextLabelFactory(parent=parent)
        tl_child_2 = TextLabelFactory(parent=parent, order=30)
        self.assertEqual(parent.order, 1)
        self.assertEqual(tl_child_1.order, 1)
        self.assertEqual(tl_child_2.order, 2)

    def test_with_one_parent_one_same_tree_level_shift_value(self):
        parent = TextLabelFactory(order=1)
        tl_child_initial_1 = TextLabelFactory(parent=parent, order=1)
        tl_child_initial_2 = TextLabelFactory(parent=parent, order=4)
        tl_child_new_2 = TextLabelFactory(parent=parent, order=2)
        tl_child_initial_1.refresh_from_db()
        tl_child_initial_2.refresh_from_db()
        self.assertEqual(parent.order, 1)
        self.assertEqual(tl_child_initial_1.order, 1)
        self.assertEqual(tl_child_initial_2.order, 3)
        self.assertEqual(tl_child_new_2.order, 2)

    def test_with_multiple_parent_one_same_tree_level_shift_value(self):
        parent_1 = TextLabelFactory(order=1)
        parent_2 = TextLabelFactory(order=2)
        parent_3 = TextLabelFactory(order=3)
        self.assertEqual(parent_1.order, 1)
        self.assertEqual(parent_2.order, 2)
        self.assertEqual(parent_3.order, 3)
        tl_child_parent_1_initial_1 = TextLabelFactory(parent=parent_1)
        tl_child_parent_1_new_1 = TextLabelFactory(parent=parent_1, order=1)
        tl_child_parent_1_initial_1.refresh_from_db()
        self.assertEqual(tl_child_parent_1_initial_1.order, 2)
        self.assertEqual(tl_child_parent_1_new_1.order, 1)
        tl_child_parent_2_initial_1 = TextLabelFactory(parent=parent_2, order=1)
        tl_child_parent_2_initial_2 = TextLabelFactory(parent=parent_2, order=2)
        self.assertEqual(tl_child_parent_2_initial_1.order, 1)
        self.assertEqual(tl_child_parent_2_initial_2.order, 2)

    def test_circular_dependency(self):
        a = TextLabelFactory()
        b = TextLabelFactory(parent=a)
        c = TextLabelFactory(parent=b)

        b.parent = c
        with self.assertRaises(ValueError):
            return b.save()

    def test_change_parent_go_up_one_level(self):
        a = TextLabelFactory()
        b = TextLabelFactory(parent=a)
        c = TextLabelFactory(parent=b)

        c.parent = a
        c.save()
        self.assertEqual(c.parent, a)
        self.assertEqual(c.order, 1)
        b.refresh_from_db()
        self.assertEqual(b.order, 2)

    def test_change_parent_go_root_recompute_child(self):
        root = TextLabelFactory()
        child_1 = TextLabelFactory(parent=root)
        child_2 = TextLabelFactory(parent=root)

        child_1.parent = None
        child_1.save()
        root.refresh_from_db()
        child_2.refresh_from_db()
        self.assertEqual(root.parent, None)
        self.assertEqual(root.order, 2)
        self.assertEqual(child_1.parent, None)
        self.assertEqual(child_1.order, 1)
        self.assertEqual(child_2.parent, root)
        self.assertEqual(child_2.order, 1)

    def test_get_by_label_or_none(self):
        text_labels = text_label.TextLabel.objects.all()
        text_labels.delete()
        txt_label = get_object_or_none(
            TextLabel,
            label='random'
        )
        self.assertIsNone(txt_label)


class TextLabelComplexeStructureTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.A = TextLabelFactory(order=1)
        cls.C = TextLabelFactory(parent=cls.A, order=2)
        cls.E = TextLabelFactory(parent=cls.C, order=1)
        cls.F = TextLabelFactory(parent=cls.C, order=2)
        cls.G = TextLabelFactory(parent=cls.C, order=3)

    def setUp(self):
        self.B = TextLabelFactory(parent=self.A, order=1)
        self.D = TextLabelFactory(parent=self.B, order=1)

    def test_move_to_root_structure(self):
        self.B.parent = None
        self.B.save()
        self.A.refresh_from_db()
        self.C.refresh_from_db()
        self.assertEqual(self.B.parent, None)
        self.assertEqual(self.B.order, 1)  # Root level
        self.assertEqual(self.A.order, 2)  # Root level
        self.assertEqual(self.C.order, 1)

    def test_change_order_second_level(self):
        self.B.order = 4  # not exist
        self.B.save()
        self.C.refresh_from_db()
        self.assertEqual(self.B.order, 2)  # Inversion
        self.assertEqual(self.C.order, 1)  # Inversion

    def test_change_on_same_level_no_change_as_result(self):
        self.E.order = 2
        self.E.save()
        self.F.refresh_from_db()
        self.G.refresh_from_db()
        # No change because we have reorder value
        self.assertEqual(self.E.order, 1)
        self.assertEqual(self.F.order, 2)
        self.assertEqual(self.G.order, 3)
