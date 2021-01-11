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

from base.forms.learning_unit.learning_unit_create import LearningUnitModelForm
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.learning_container import LearningContainerFactory


class TestLearningUnitModelFormSave(TestCase):
    """Tests LearningUnitModelForm.save()"""

    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.learning_container = LearningContainerFactory()
        cls.form = LearningUnitModelForm()
        cls.save_kwargs = {'learning_container': cls.learning_container,
                           'start_year': cls.current_academic_year}

    def test_case_missing_learning_container_kwarg(self):
        with self.assertRaises(KeyError):
            self.form.save(academic_year=self.current_academic_year)

    def test_case_missing_academic_year_kwarg(self):
        with self.assertRaises(KeyError):
            self.form.save(learning_container=self.learning_container)
