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
from django.conf import settings
from django.test import TestCase

from base.tests.factories.education_group_year import EducationGroupYearFactory, EducationGroupYearCommonFactory
from cms.enums.entity_name import OFFER_YEAR
from cms.models.translated_text import TranslatedText
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextRandomFactory
from cms.tests.factories.translated_text_label import TranslatedTextLabelFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from webservices import business


class EnsureKeyTestCase(TestCase):
    def test_evaluation_key(self):
        self.assertEqual(business.EVALUATION_KEY, 'evaluation')

        
class GetEvaluationTestCase(TestCase):
    def setUp(self):
        self.education_group_year = EducationGroupYearFactory(acronym='ACTU2M')

        common_education_group_year = EducationGroupYearCommonFactory(
            academic_year=self.education_group_year.academic_year
        )
        self.cms_label_name = 'evaluation'

        text_label = TextLabelFactory(entity=OFFER_YEAR, label='evaluation')
        TranslatedTextLabelFactory(text_label=text_label,
                                   language=settings.LANGUAGE_CODE_FR)
        self.evaluation = TranslatedTextRandomFactory(text_label=text_label,
                                                      language=settings.LANGUAGE_CODE_FR,
                                                      reference=self.education_group_year.id,
                                                      entity=text_label.entity)

        self.common = TranslatedTextRandomFactory(text_label=text_label,
                                                  language=settings.LANGUAGE_CODE_FR,
                                                  reference=common_education_group_year.id,
                                                  entity=text_label.entity)

    def test_get_evaluation_french_version(self):
        label, text = business.get_evaluation_text(self.education_group_year, settings.LANGUAGE_CODE_FR)
        self.assertEqual(text, self.evaluation.text)

    def test_get_evaluation_no_english_version(self):
        with self.assertRaises(TranslatedText.DoesNotExist):
            business.get_evaluation_text(self.education_group_year, settings.LANGUAGE_CODE_EN)


class GetContactsIntroTextTestCase(TestCase):
    def setUp(self):
        self.education_group_year = EducationGroupYearFactory()
        self.node = NodeGroupYearFactory(
            code=self.education_group_year.partial_acronym,
            year=self.education_group_year.academic_year.year,
            node_type=self.education_group_year.education_group_type,
        )
        self.cms_label_name = business.CONTACT_INTRO_KEY

        text_label = TextLabelFactory(entity=OFFER_YEAR, label=self.cms_label_name)
        self.contact_intro_fr = TranslatedTextRandomFactory(
            text_label=text_label,
            language=settings.LANGUAGE_CODE_FR,
            reference=self.education_group_year.id,
            entity=text_label.entity
        )
        self.contact_intro_en = TranslatedTextRandomFactory(
            text_label=text_label,
            language=settings.LANGUAGE_CODE_EN,
            reference=self.education_group_year.id,
            entity=text_label.entity
        )

    def test_get_contacts_intro_text_case_no_value(self):
        education_group_year = EducationGroupYearFactory()
        node = NodeGroupYearFactory(
            node_type=education_group_year.education_group_type,
            code=education_group_year.partial_acronym,
            year=education_group_year.academic_year.year
        )
        self.assertIsNone(business.get_contacts_intro_text(node, settings.LANGUAGE_CODE_FR))

    def test_get_contacts_intro_text_case_french_version(self):
        intro_text = business.get_contacts_intro_text(self.node, settings.LANGUAGE_CODE_FR)
        self.assertEqual(intro_text, self.contact_intro_fr.text)

    def test_get_contacts_intro_text_case_english_version(self):
        intro_text = business.get_contacts_intro_text(self.node, settings.LANGUAGE_CODE_EN)
        self.assertEqual(intro_text, self.contact_intro_en.text)
