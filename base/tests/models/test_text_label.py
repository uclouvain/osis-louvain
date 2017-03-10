##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase
from base.models import text_label
from base.enums import entity_name
from base.models.exceptions import TxtLabelOrderMustExitsException


def create_text_label(entity_name, part_of, label, order, published):
    a_text_label = text_label.TextLabel(entity_name=entity_name, part_of=part_of, label=label, order=order,
                                        published=published)
    a_text_label.save()
    return a_text_label


class TextLabelTest(TestCase):

    def setUp(self):
        self.txtlabel10 = create_text_label(entity_name=entity_name.LEARNING_UNIT_YEAR,
                                            part_of=None, label="WINDOW", order=10, published=True)
        self.txtlabel11 = create_text_label(entity_name=entity_name.LEARNING_UNIT_YEAR,
                                            part_of=self.txtlabel10, label="SUBWINDOW_A", order=1, published=True)
        self.txtlabel12 = create_text_label(entity_name=entity_name.LEARNING_UNIT_YEAR,
                                            part_of=self.txtlabel10, label="SUBWINDOW_B", order=2,
                                            published=True)
        self.txtlabel13 = create_text_label(entity_name=entity_name.LEARNING_UNIT_YEAR,
                                            part_of=self.txtlabel10, label="SUBWINDOW_C", order=3, published=True)

    def test_insert_new_text_label_same_order(self):
        txtlabel14 = text_label.TextLabel(entity_name=entity_name.LEARNING_UNIT_YEAR,
                                          part_of=self.txtlabel10, label="SUBWINDOW_CC", order=3, published=True)
        self.assertEqual(txtlabel14.save(), None)

    def test_insert_new_text_label_without_order(self):
        txtlabel15 = text_label.TextLabel(entity_name=entity_name.LEARNING_UNIT_YEAR,
                                          part_of=self.txtlabel10, label="SUBWINDOW_CC", published=True)
        self.assertRaises(TxtLabelOrderMustExitsException, txtlabel15.save)
