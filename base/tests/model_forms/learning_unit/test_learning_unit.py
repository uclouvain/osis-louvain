##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.utils.translation import ugettext_lazy as _

from base.forms.learning_unit.learning_unit_create import LearningUnitModelForm
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.learning_unit_periodicity import BIENNIAL_EVEN, ANNUAL
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.learning_container import LearningContainerFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory


class TestLearningUnitModelFormInit(TestCase):
    """Tests LearningUnitModelForm.__init__()"""
    def setUp(self):
        self.form = LearningUnitModelForm()

    def test_faculty_remark_widget_textarea_rows(self):
        self.assertEqual(self.form.fields['faculty_remark'].widget.attrs['rows'], '5', "should assert rows == 5")

    def test_other_remark_widget_textarea_rows(self):
        self.assertEqual(self.form.fields['other_remark'].widget.attrs['rows'], '5', "should assert rows == 5")


class TestLearningUnitModelFormSave(TestCase):
    """Tests LearningUnitModelForm.save()"""

    quote_1 = """Many that live deserve death. 
    And some that die deserve life. 
    Can you give it to them? 
    Then do not be too eager to deal out death in judgement."""

    quote_2 = """And then her heart changed, or at least she understood it; 
    and the winter passed, and the sun shone upon her."""

    post_data = {'periodicity': BIENNIAL_EVEN, 'faculty_remark': quote_1, 'other_remark': quote_2}

    def setUp(self):
        self.current_academic_year = create_current_academic_year()
        self.learning_container = LearningContainerFactory()
        self.form = LearningUnitModelForm(self.post_data)
        self.save_kwargs = {'learning_container': self.learning_container,
                            'start_year': self.current_academic_year.year}

    def test_case_missing_learning_container_kwarg(self):
        with self.assertRaises(KeyError):
            self.form.save(academic_year=self.current_academic_year)

    def test_case_missing_academic_year_kwarg(self):
        with self.assertRaises(KeyError):
            self.form.save(learning_container=self.learning_container)

    def test_case_creation_correctly_saved(self):
        self.assertTrue(self.form.is_valid(), self.form.errors)
        lu = self.form.save(**self.save_kwargs)
        self.assertEqual(lu.periodicity, BIENNIAL_EVEN)
        self.assertEqual(lu.faculty_remark, self.quote_1)
        self.assertEqual(lu.other_remark, self.quote_2)

    def test_case_update_correctly_saved(self):
        learning_unit_to_update = LearningUnitFactory(learning_container=self.learning_container)
        self.form = LearningUnitModelForm(self.post_data, instance=learning_unit_to_update)
        self.assertTrue(self.form.is_valid(), self.form.errors)
        lu = self.form.save(**self.save_kwargs)
        self.assertEqual(lu.periodicity, BIENNIAL_EVEN)
        self.assertEqual(lu.faculty_remark, self.quote_1)
        self.assertEqual(lu.other_remark, self.quote_2)

    def test_full_periodicity_biannual_with_partim_annual(self):
        a_new_learning_unit_full = LearningUnitYearFactory(
            academic_year=self.current_academic_year,
            subtype=learning_unit_year_subtypes.FULL,
            credits=20)
        a_new_learning_unit_partim = LearningUnitYearFactory(
            academic_year=self.current_academic_year,
            subtype=learning_unit_year_subtypes.PARTIM,
            credits=12)

        a_new_learning_unit_partim.learning_unit.learning_container = a_new_learning_unit_full.\
            learning_unit.learning_container
        a_new_learning_unit_partim.learning_container_year = a_new_learning_unit_full.learning_container_year
        a_new_learning_unit_partim.learning_unit.save()
        a_new_learning_unit_partim.save()

        a_new_learning_unit_partim.learning_unit.periodicity = ANNUAL
        a_new_learning_unit_partim.learning_unit.save()

        post_data = {'periodicity': BIENNIAL_EVEN}
        form = LearningUnitModelForm(data=post_data, instance=a_new_learning_unit_full.learning_unit)

        # The form should be valid
        self.assertFalse(form.is_valid(), form.errors)
        self.assertEqual(form.errors.get('periodicity'),
                         [_('The periodicity of the parent and the partims do not match')])
