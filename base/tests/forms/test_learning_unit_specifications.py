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
from django.test import TestCase

from base.forms.learning_unit_specifications import LearningUnitSpecificationsEditForm
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from cms.models.translated_text import TranslatedText
from cms.tests.factories.translated_text import TranslatedTextFactory


class TestLearningSpecificationsForm(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.learning_unit_year = LearningUnitYearFactory(
            academic_year=create_current_academic_year()
        )
        cls.laa = TranslatedTextFactory(
            reference=cls.learning_unit_year.id
        )
        cls.laa_en = TranslatedTextFactory(
            reference=cls.learning_unit_year.id
        )

    def test_valid_form_and_save_correctly_text(self):
        data = {
            'trans_text_fr': 'FR_TEXT',
            'trans_text_en': 'EN_TEXT',
            'cms_fr_id': self.laa.id,
            'cms_en_id': self.laa_en.id
        }
        form = LearningUnitSpecificationsEditForm(
            learning_unit_year=self.learning_unit_year,
            data=data
        )
        form.load_initial()
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        text_fr = TranslatedText.objects.get(id=self.laa.id)
        self.assertEqual(text_fr.text, 'FR_TEXT')
        text_en = TranslatedText.objects.get(id=self.laa_en.id)
        self.assertEqual(text_en.text, 'EN_TEXT')
