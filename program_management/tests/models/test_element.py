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
from django.db import IntegrityError
from django.test import TestCase
from django.utils.translation import gettext as _

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from education_group.tests.factories.group import GroupFactory
from education_group.tests.factories.group_year import GroupYearFactory
from learning_unit.tests.factories.learning_class_year import LearningClassYearFactory
from program_management.models.element import Element
from program_management.tests.factories.element import ElementFactory, ElementLearningClassYearFactory, \
    ElementGroupYearFactory


class TestElementSave(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.luy = LearningUnitYearFactory(academic_year=cls.academic_year)
        cls.lcy = LearningClassYearFactory()
        cls.gy = GroupYearFactory(academic_year=cls.academic_year, group=GroupFactory(start_year=cls.academic_year))

    def test_save_no_foreign_key_set(self):
        with self.assertRaises(IntegrityError):
            element = ElementFactory.build()
            element.save()

    def test_save_one_group_year_fk(self):
        element = ElementGroupYearFactory.build(group_year=self.gy)
        element.save()

        self.assertTrue(
            Element.objects.filter(group_year=self.gy).exists()
        )

    def test_save_one_learning_unit_year_fk(self):
        learning_unit_year = LearningUnitYearFactory(academic_year=self.academic_year)
        self.assertTrue(
            Element.objects.filter(learning_unit_year=learning_unit_year).exists()
        )

    def test_save_one_learning_class_year_fk(self):
        element = ElementLearningClassYearFactory.build(learning_class_year=self.lcy)
        element.save()

        self.assertTrue(
            Element.objects.filter(learning_class_year=self.lcy).exists()
        )

    def test_save_more_than_one_fk(self):
        with self.assertRaises(IntegrityError):
            element = ElementFactory.build(learning_class_year=self.lcy, group_year=self.gy)
            element.save()

    def test_str_luy(self):
        element = ElementFactory(learning_unit_year=self.luy)
        self.assertEqual(str(element), str(self.luy))

    def test_str_gy(self):
        element = ElementFactory(group_year=self.gy)
        self.assertEqual(str(element), str(self.gy))

    def test_str_lcy(self):
        element = ElementFactory(learning_class_year=self.lcy)
        self.assertEqual(str(element), str(self.lcy))
