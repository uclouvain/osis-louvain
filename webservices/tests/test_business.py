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

from base.models.enums.publication_contact_type import PublicationContactType
from base.tests.factories.education_group_achievement import EducationGroupAchievementFactory
from base.tests.factories.education_group_detailed_achievement import EducationGroupDetailedAchievementFactory
from base.tests.factories.education_group_publication_contact import EducationGroupPublicationContactFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, EducationGroupYearCommonFactory
from cms.enums import entity_name
from cms.enums.entity_name import OFFER_YEAR
from cms.models.translated_text import TranslatedText
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory, TranslatedTextRandomFactory
from cms.tests.factories.translated_text_label import TranslatedTextLabelFactory
from webservices import business


class EnsureKeyTestCase(TestCase):
    def test_skills_and_achievement_key(self):
        self.assertEqual(business.SKILLS_AND_ACHIEVEMENTS_KEY, 'comp_acquis')

    def test_skills_and_achievement_data(self):
        self.assertEqual(business.SKILLS_AND_ACHIEVEMENTS_AA_DATA, 'achievements')

    def test_evaluation_key(self):
        self.assertEqual(business.EVALUATION_KEY, 'evaluation')


class GetAchievementsTestCase(TestCase):
    def setUp(self):
        self.education_group_year = EducationGroupYearFactory()
        self.education_group_achievement = EducationGroupAchievementFactory(
            education_group_year=self.education_group_year
        )
        self.education_group_detailed_achievement = EducationGroupDetailedAchievementFactory(
            education_group_achievement=self.education_group_achievement
        )

    def test_get_achievements_case_get_english_version(self):
        achievements_list = business.get_achievements(self.education_group_year, settings.LANGUAGE_CODE_EN)

        self.assertIsInstance(achievements_list, list)
        self.assertEqual(len(achievements_list), 1)

        achievement = achievements_list[0]
        self.assertEqual(achievement['teaser'], self.education_group_achievement.english_text)
        self.assertTrue(len(achievement['detailed_achievements']), 1)

        detailed_achievement = achievement['detailed_achievements'][0]
        self.assertEqual(detailed_achievement['text'], self.education_group_detailed_achievement.english_text)
        self.assertEqual(detailed_achievement['code_name'], self.education_group_detailed_achievement.code_name)

    def test_get_achievements_case_get_french_version(self):
        achievements_list = business.get_achievements(self.education_group_year, settings.LANGUAGE_CODE_FR)

        self.assertIsInstance(achievements_list, list)
        self.assertEqual(len(achievements_list), 1)

        achievement = achievements_list[0]
        self.assertEqual(achievement['teaser'], self.education_group_achievement.french_text)

        self.assertTrue(len(achievement['detailed_achievements']), 1)
        detailed_achievement = achievement['detailed_achievements'][0]
        self.assertEqual(detailed_achievement['text'], self.education_group_detailed_achievement.french_text)
        self.assertEqual(detailed_achievement['code_name'], self.education_group_detailed_achievement.code_name)

    def test_get_achievements_case_language_code_not_supported(self):
        with self.assertRaises(AttributeError):
            business.get_achievements(self.education_group_year, 'dummy-language')

    def test_get_achievements_case_no_detailed_achievement(self):
        self.education_group_detailed_achievement.delete()

        achievements_list = business.get_achievements(self.education_group_year, settings.LANGUAGE_CODE_FR)
        self.assertIsInstance(achievements_list, list)
        self.assertEqual(len(achievements_list), 1)

        achievement = achievements_list[0]
        self.assertIsNone(achievement['detailed_achievements'])


class GetIntroExtraContentAchievementsTestCase(TestCase):
    def setUp(self):
        self.cms_label_name = 'skills_and_achievements_introduction'
        self.education_group_year = EducationGroupYearFactory()
        self.introduction = TranslatedTextFactory(
            entity=entity_name.OFFER_YEAR,
            reference=self.education_group_year.pk,
            language=settings.LANGUAGE_CODE_EN,
            text_label__label=self.cms_label_name
        )

    def test_get_achievements_case_get_english_version(self):
        intro_extra_content = business.get_intro_extra_content_achievements(
            self.education_group_year,
            settings.LANGUAGE_CODE_EN
        )

        self.assertIsInstance(intro_extra_content, dict)
        self.assertEqual(intro_extra_content[self.cms_label_name], self.introduction.text)

    def test_get_achievements_case_get_french_version_no_results(self):
        intro_extra_content = business.get_intro_extra_content_achievements(
            self.education_group_year,
            settings.LANGUAGE_CODE_FR
        )
        self.assertIsInstance(intro_extra_content, dict)
        self.assertDictEqual(intro_extra_content, {})

        
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

    def test_get_common_evaluation_french_version(self):
        text = business.get_common_evaluation_text(self.education_group_year, settings.LANGUAGE_CODE_FR)
        self.assertEqual(text, self.common.text)

    def test_get__common_evaluation_no_english_version(self):
        with self.assertRaises(TranslatedText.DoesNotExist):
            business.get_common_evaluation_text(self.education_group_year, settings.LANGUAGE_CODE_EN)


class GetContactsGroupByTypesTestCase(TestCase):
    def setUp(self):
        self.education_group_year = EducationGroupYearFactory()

        self.academic_responsible_1 = EducationGroupPublicationContactFactory(
            type=PublicationContactType.ACADEMIC_RESPONSIBLE.name,
            education_group_year=self.education_group_year,
            order=0
        )
        self.academic_responsible_2 = EducationGroupPublicationContactFactory(
            type=PublicationContactType.ACADEMIC_RESPONSIBLE.name,
            education_group_year=self.education_group_year,
            order=1
        )

    def test_get_contacts_group_by_types_no_data(self):
        education_group_year = EducationGroupYearFactory()
        self.assertDictEqual(
            business.get_contacts_group_by_types(education_group_year, settings.LANGUAGE_CODE_FR),
            {}
        )

    def test_get_contacts_group_by_types_assert_order(self):
        results = business.get_contacts_group_by_types(self.education_group_year, settings.LANGUAGE_CODE_FR)

        self.assertIsInstance(results, dict)
        self.assertTrue(results['academic_responsibles'])

        academic_responsibles = results['academic_responsibles']
        self.assertIsInstance(academic_responsibles, list)
        self.assertEqual(len(academic_responsibles), 2)

        self.assertEqual(academic_responsibles[0]['email'], self.academic_responsible_1.email)
        self.assertEqual(academic_responsibles[1]['email'], self.academic_responsible_2.email)

        # Swap result...
        self.academic_responsible_2.up()

        results = business.get_contacts_group_by_types(self.education_group_year, settings.LANGUAGE_CODE_FR)
        academic_responsibles = results['academic_responsibles']
        self.assertEqual(academic_responsibles[0]['email'], self.academic_responsible_2.email)
        self.assertEqual(academic_responsibles[1]['email'], self.academic_responsible_1.email)

    def test_get_contacts_group_by_types_assert_french_returned(self):
        results = business.get_contacts_group_by_types(self.education_group_year, settings.LANGUAGE_CODE_FR)
        academic_responsibles = results['academic_responsibles']
        self.assertEqual(academic_responsibles[0]['role'], self.academic_responsible_1.role_fr)
        self.assertEqual(academic_responsibles[1]['role'], self.academic_responsible_2.role_fr)

    def test_get_contacts_group_by_types_assert_english_returned(self):
        results = business.get_contacts_group_by_types(self.education_group_year, settings.LANGUAGE_CODE_EN)
        academic_responsibles = results['academic_responsibles']
        self.assertEqual(academic_responsibles[0]['role'], self.academic_responsible_1.role_en)
        self.assertEqual(academic_responsibles[1]['role'], self.academic_responsible_2.role_en)

    def test_get_contacts_group_by_types_assert_empty_str_as_null(self):
        self.academic_responsible_1.role_fr = ''
        self.academic_responsible_1.description = ''
        self.academic_responsible_1.save()

        results = business.get_contacts_group_by_types(self.education_group_year, settings.LANGUAGE_CODE_FR)
        academic_responsibles = results['academic_responsibles']
        self.assertIsNone(academic_responsibles[0]['role'])
        self.assertIsNone(academic_responsibles[0]['description'])


class GetContactsIntroTextTestCase(TestCase):
    def setUp(self):
        self.education_group_year = EducationGroupYearFactory()
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
        self.assertIsNone(business.get_contacts_intro_text(education_group_year, settings.LANGUAGE_CODE_FR))

    def test_get_contacts_intro_text_case_french_version(self):
        intro_text = business.get_contacts_intro_text(self.education_group_year, settings.LANGUAGE_CODE_FR)
        self.assertEqual(intro_text, self.contact_intro_fr.text)

    def test_get_contacts_intro_text_case_english_version(self):
        intro_text = business.get_contacts_intro_text(self.education_group_year, settings.LANGUAGE_CODE_EN)
        self.assertEqual(intro_text, self.contact_intro_en.text)
