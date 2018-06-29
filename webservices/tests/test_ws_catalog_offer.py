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

from django.test import TestCase

from base.models.admission_condition import AdmissionCondition, AdmissionConditionLine
from base.tests.factories.education_group_year import EducationGroupYearFactory
from cms.enums.entity_name import OFFER_YEAR
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextRandomFactory
from cms.tests.factories.translated_text_label import TranslatedTextLabelFactory
from webservices.tests.helper import Helper
from webservices.utils import convert_sections_list_of_dict_to_dict


def remove_conditions_admission(sections):
    result = []
    condition_admission_section = None

    for section in sections:
        if section['id'] == 'conditions_admission':
            condition_admission_section = section
        else:
            result.append(section)
    return result, condition_admission_section


class WsCatalogOfferPostTestCase(TestCase, Helper):
    URL_NAME = 'v0.1-ws_catalog_offer'
    maxDiff = None

    def test_year_not_found(self):
        response = self.post(1990, 'fr', 'actu2m', data={})
        self.assertEqual(response.status_code, 404)

    def test_string_year_not_found(self):
        response = self.post('1990', 'fr', 'actu2m', data={})
        self.assertEqual(response.status_code, 404)

    def test_language_not_found(self):
        response = self.post(2017, 'ch', 'actu2m', data={})
        self.assertEqual(response.status_code, 404)

    def test_acronym_not_found(self):
        response = self.post(2017, 'fr', 'XYZ', data={})
        self.assertEqual(response.status_code, 404)

    def test_first_based_on_the_original_message(self):
        education_group_year = EducationGroupYearFactory(acronym='ACTU2M')

        common_education_group_year = EducationGroupYearFactory(
            acronym='common',
            academic_year=education_group_year.academic_year
        )

        iso_language, language = 'fr-be', 'fr'

        message = {
            'anac': str(education_group_year.academic_year.year),
            'code_offre': education_group_year.acronym,
            "sections": [
                "welcome_job",
                "welcome_profil",
                "welcome_programme",
                "welcome_introduction",
                "cond_admission",
                "infos_pratiques",
                "caap",
                "caap-commun",
                "contacts",
                "structure",
                "acces_professions",
                "comp_acquis",
                "pedagogie",
                "formations_accessibles",
                "evaluation",
                "mobilite",
                "programme_detaille",
                "certificats",
                "module_complementaire",
                "module_complementaire-commun",
                "prerequis",
                "prerequis-commun",
                "intro-lactu200t",
                "intro-lactu200s",
                "options",
                "intro-lactu200o",
                "intro-lsst100o"
            ]
        }

        ega = EducationGroupYearFactory(partial_acronym='lactu200t',
                                        academic_year=education_group_year.academic_year)
        text_label = TextLabelFactory(entity=OFFER_YEAR, label='intro')
        TranslatedTextLabelFactory(text_label=text_label,
                                   language=iso_language)
        TranslatedTextRandomFactory(text_label=text_label,
                                    language=iso_language,
                                    reference=ega.id,
                                    entity=text_label.entity)

        text_label = TextLabelFactory(entity=OFFER_YEAR, label='prerequis')
        TranslatedTextLabelFactory(text_label=text_label,
                                   language=iso_language)
        TranslatedTextRandomFactory(text_label=text_label,
                                    language=iso_language,
                                    reference=education_group_year.id,
                                    entity=text_label.entity)

        TranslatedTextRandomFactory(text_label=text_label,
                                    language=iso_language,
                                    reference=common_education_group_year.id,
                                    entity=text_label.entity)

        text_label = TextLabelFactory(entity=OFFER_YEAR, label='caap')
        TranslatedTextLabelFactory(text_label=text_label,
                                   language=iso_language)
        TranslatedTextRandomFactory(text_label=text_label,
                                    language=iso_language,
                                    reference=education_group_year.id,
                                    entity=text_label.entity)

        TranslatedTextRandomFactory(text_label=text_label,
                                    language=iso_language,
                                    reference=common_education_group_year.id,
                                    entity=text_label.entity)

        response = self.post(
            education_group_year.academic_year.year,
            language,
            education_group_year.acronym,
            data=message,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

    def test_without_any_sections(self):
        education_group_year = EducationGroupYearFactory(acronym='actu2m')

        common_education_group_year = EducationGroupYearFactory(
            acronym='common',
            academic_year=education_group_year.academic_year,
        )

        text_label = TextLabelFactory(entity=OFFER_YEAR)

        for iso_language, language in [('fr-be', 'fr'), ('en', 'en')]:
            with self.subTest(iso_language=iso_language, language=language):
                TranslatedTextLabelFactory(text_label=text_label,
                                           language=iso_language)
                TranslatedTextRandomFactory(text_label=text_label,
                                            language=iso_language,
                                            reference=common_education_group_year.id,
                                            entity=text_label.entity)
                message = {
                    'anac': str(education_group_year.academic_year.year),
                    'code_offre': education_group_year.acronym,
                    'sections': [
                        'welcome_job',
                    ]
                }

                response = self.post(
                    education_group_year.academic_year.year,
                    language,
                    education_group_year.acronym,
                    data=message
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content_type, 'application/json')

                response_json = response.json()
                sections, conditions_admission_section = remove_conditions_admission(response_json['sections'])
                response_json['sections'] = sections

                title_to_test = education_group_year.title if language == 'fr' else education_group_year.title_english
                self.assertDictEqual(response_json, {
                    'acronym': education_group_year.acronym,
                    'language': language,
                    'title': title_to_test,
                    'sections': [],
                    'year': education_group_year.academic_year.year,
                })

    def test_with_one_section(self):
        education_group_year = EducationGroupYearFactory(acronym='actu2m')

        text_label = TextLabelFactory(entity=OFFER_YEAR, label='caap')

        for iso_language, language in [('fr-be', 'fr'), ('en', 'en')]:
            with self.subTest(iso_language=iso_language, language=language):
                ttl = TranslatedTextLabelFactory(text_label=text_label,
                                                 language=iso_language)
                tt = TranslatedTextRandomFactory(text_label=text_label,
                                                 language=iso_language,
                                                 reference=education_group_year.id,
                                                 entity=text_label.entity)

                message = {
                    'code_offre': education_group_year.acronym,
                    'anac': str(education_group_year.academic_year.year),
                    'sections': [
                        text_label.label,
                    ]
                }

                response = self.post(
                    education_group_year.academic_year.year,
                    language,
                    education_group_year.acronym,
                    data=message
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content_type, 'application/json')

                response_json = response.json()
                sections, conditions_admission_section = remove_conditions_admission(response_json['sections'])
                response_json['sections'] = sections

                title_to_test = education_group_year.title if language == 'fr' else education_group_year.title_english

                self.assertDictEqual(response_json, {
                    'acronym': education_group_year.acronym,
                    'language': language,
                    'title': title_to_test,
                    'year': education_group_year.academic_year.year,
                    'sections': [
                        {
                            'label': ttl.label,
                            'id': tt.text_label.label,
                            'content': tt.text,
                        }
                    ]
                })

    def test_with_one_section_with_common(self):
        education_group_year = EducationGroupYearFactory(acronym='actu2m')

        common_education_group_year = EducationGroupYearFactory(
            acronym='common',
            academic_year=education_group_year.academic_year,
        )

        text_label = TextLabelFactory(entity=OFFER_YEAR, label='caap')

        for iso_language, language in [('fr-be', 'fr'), ('en', 'en')]:
            with self.subTest(iso_language=iso_language, language=language):
                ttl = TranslatedTextLabelFactory(text_label=text_label,
                                                 language=iso_language)
                tt = TranslatedTextRandomFactory(text_label=text_label,
                                                 language=iso_language,
                                                 reference=education_group_year.id,
                                                 entity=text_label.entity)

                tt2 = TranslatedTextRandomFactory(text_label=text_label,
                                                  language=iso_language,
                                                  reference=common_education_group_year.id,
                                                  entity=text_label.entity)

                message = {
                    'code_offre': education_group_year.acronym,
                    'anac': str(education_group_year.academic_year.year),
                    'sections': [
                        text_label.label,
                        text_label.label + '-commun'
                    ]
                }

                response = self.post(
                    education_group_year.academic_year.year,
                    language,
                    education_group_year.acronym,
                    data=message
                )

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content_type, 'application/json')

                response_json = response.json()

                title_to_test = education_group_year.title if language == 'fr' else education_group_year.title_english

                sections, conditions_admission_section = remove_conditions_admission(response_json.pop('sections', []))
                response_sections = convert_sections_list_of_dict_to_dict(sections)

                self.assertDictEqual(response_json, {
                    'acronym': education_group_year.acronym,
                    'language': language,
                    'title': title_to_test,
                    'year': education_group_year.academic_year.year,
                })

                sections = [{
                    'id': tt.text_label.label,
                    'label': ttl.label,
                    'content': tt.text,
                }, {
                    'id': tt.text_label.label + '-commun',
                    'label': ttl.label,
                    'content': tt2.text,
                }]
                sections = convert_sections_list_of_dict_to_dict(sections)

                self.assertDictEqual(response_sections, sections)

    def test_global(self):
        education_group_year = EducationGroupYearFactory(acronym='ACTU2M')

        common_education_group_year = EducationGroupYearFactory(
            acronym='common',
            academic_year=education_group_year.academic_year
        )

        iso_language, language = 'fr-be', 'fr'

        sections = [
            "welcome_job",
            "welcome_profil",
            "welcome_programme",
            "welcome_introduction",
            "cond_admission",
            "infos_pratiques",
            "caap",
            "caap-commun",
            "contacts",
            "structure",
            "acces_professions",
            "comp_acquis",
            "pedagogie",
            "formations_accessibles",
            "evaluation",
            "mobilite",
            "programme_detaille",
            "certificats",
            "module_complementaire",
            "module_complementaire-commun",
            "prerequis",
            "prerequis-commun",
            "intro-lactu200t",
            "intro-lactu200s",
            "options",
            "intro-lactu200o",
            "intro-lsst100o"
        ]

        sections_set, common_sections_set, intro_set = set(), set(), set()

        for section in sections:
            if section.startswith('intro-'):
                intro_set.add(section[len('intro-'):])
                continue
            if section.endswith('-commun'):
                section = section[:-len('-commun')]
                common_sections_set.add(section)
            sections_set.add(section)

        self.assertEqual(len(common_sections_set), 3)
        self.assertEqual(len(intro_set), 4)

        for section in sections_set:
            text_label = TextLabelFactory(entity=OFFER_YEAR, label=section)
            TranslatedTextLabelFactory(text_label=text_label, language=iso_language)

            TranslatedTextRandomFactory(text_label=text_label,
                                        language=iso_language,
                                        reference=education_group_year.id,
                                        entity=text_label.entity,
                                        text='<tag>{section}</tag>'.format(section=section))

            if section in common_sections_set:
                TranslatedTextRandomFactory(text_label=text_label,
                                            language=iso_language,
                                            reference=common_education_group_year.id,
                                            entity=text_label.entity,
                                            text='<tag>{section}-commun</tag>'.format(section=section))

        text_label = TextLabelFactory(entity=OFFER_YEAR, label='intro')
        TranslatedTextLabelFactory(text_label=text_label,
                                   language=iso_language)

        for section in intro_set:
            ega = EducationGroupYearFactory(partial_acronym=section, academic_year=education_group_year.academic_year)
            TranslatedTextRandomFactory(text_label=text_label,
                                        language=iso_language,
                                        reference=ega.id,
                                        entity=text_label.entity,
                                        text='<tag>intro-{section}</tag>'.format(section=section))

        message = {
            'anac': str(education_group_year.academic_year.year),
            'code_offre': education_group_year.acronym,
            "sections": sections,
        }

        response = self.post(
            education_group_year.academic_year.year,
            language,
            education_group_year.acronym,
            data=message,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response_json = response.json()

        sections, conditions_admission_section = remove_conditions_admission(response_json['sections'])
        response_sections = convert_sections_list_of_dict_to_dict(sections)

        for section in sections_set:
            if section in response_sections:
                response_sections.pop(section)

        self.assertEqual(len(response_sections), len(intro_set) + len(common_sections_set))
        for section in common_sections_set:
            if section + '-commun' in response_sections:
                response_sections.pop(section + '-commun')

        self.assertEqual(len(response_sections), len(intro_set))
        for section in intro_set:
            if 'intro-' + section in response_sections:
                response_sections.pop('intro-' + section)

        self.assertEqual(len(response_sections), 0)

    def test_no_translation_for_term(self):
        education_group_year = EducationGroupYearFactory(acronym='actu2m')

        iso_language, language = 'fr-be', 'fr'

        text_label = TextLabelFactory(entity=OFFER_YEAR)
        translated_text_label = TranslatedTextLabelFactory(text_label=text_label, language=iso_language)

        message = {
            'anac': str(education_group_year.academic_year.year),
            'code_offre': education_group_year.acronym,
            'sections': [text_label.label]
        }

        response = self.post(
            year=education_group_year.academic_year.year,
            language=language,
            acronym=education_group_year.acronym,
            data=message
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response_json = response.json()
        sections, conditions_admission_section = remove_conditions_admission(response_json['sections'])
        response_sections = convert_sections_list_of_dict_to_dict(sections)

        sections = convert_sections_list_of_dict_to_dict([{
            'id': text_label.label,
            'label': translated_text_label.label,
            'content': None
        }])

        self.assertEqual(response_sections, sections)

    def test_no_corresponding_term(self):
        education_group_year = EducationGroupYearFactory(acronym='actu2m')

        message = {
            'anac': str(education_group_year.academic_year.year),
            'code_offre': education_group_year.acronym,
            'sections': ['demo']
        }

        response = self.post(
            year=education_group_year.academic_year.year,
            language='fr',
            acronym=education_group_year.acronym,
            data=message
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response_json = response.json()
        sections, conditions_admission_section = remove_conditions_admission(response_json['sections'])
        response_sections = convert_sections_list_of_dict_to_dict(sections)

        self.assertEqual(len(response_sections), 0)


class WsOfferCatalogAdmissionsCondition(TestCase, Helper):
    URL_NAME = 'v0.1-ws_catalog_offer'

    def test_admission_conditions_for_bachelors_without_common(self):
        education_group_year = EducationGroupYearFactory(acronym='hist1ba')

        iso_language, language = 'fr-be', 'fr'

        message = {
            'anac': education_group_year.academic_year.year,
            'code_offre': education_group_year.acronym,
            'sections': [
                'conditions_admissions',
            ]
        }
        response = self.post(education_group_year.academic_year.year,
                             language,
                             education_group_year.acronym,
                             data=message)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response_json = response.json()

        useless, condition_admissions_section = remove_conditions_admission(response_json['sections'])

        self.assertDictEqual(condition_admissions_section, {
            'id': 'conditions_admission',
            'label': 'conditions_admission',
            'content': None,
        })

    def test_admission_conditions_for_bacherlors_with_common(self):
        education_group_year = EducationGroupYearFactory(acronym='hist1ba')

        education_group_year_common = EducationGroupYearFactory(acronym='common-bacs',
                                                                academic_year=education_group_year.academic_year)

        admission_condition_common = AdmissionCondition.objects.create(
            education_group_year=education_group_year_common,
            text_bachelor='this is a test')

        iso_language, language = 'fr-be', 'fr'

        message = {
            'anac': education_group_year.academic_year.year,
            'code_offre': education_group_year.acronym,
            'sections': [
                'conditions_admissions',
            ]
        }
        response = self.post(education_group_year.academic_year.year,
                             language,
                             education_group_year.acronym,
                             data=message)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response_json = response.json()

        useless, condition_admissions_section = remove_conditions_admission(response_json['sections'])

        self.assertDictEqual(condition_admissions_section, {
            'id': 'conditions_admission',
            'label': 'conditions_admission',
            'content': {'bachelor_text': 'this is a test'}
        })

    def test_admission_conditions_for_master(self):
        education_group_year = EducationGroupYearFactory(acronym='actu2m')

        admission_condition = AdmissionCondition.objects.create(education_group_year=education_group_year)
        admission_condition.text_university_bachelors = 'text_university_bachelors'
        admission_condition.save()

        education_group_year_common = EducationGroupYearFactory(acronym='common-2m',
                                                                academic_year=education_group_year.academic_year)

        admission_condition_common = AdmissionCondition.objects.create(education_group_year=education_group_year_common)
        admission_condition_common.text_free = 'text_free'
        admission_condition_common.text_personalized_access = 'text_personalized_access'
        admission_condition_common.text_adults_taking_up_university_training = 'text_adults_taking_up_university_training'
        admission_condition_common.text_admission_enrollment_procedures = 'text_admission_enrollment_procedures'
        admission_condition_common.save()

        iso_language, language = 'fr-be', 'fr'

        message = {
            'anac': education_group_year.academic_year.year,
            'code_offre': education_group_year.acronym,
            'sections': [
                'conditions_admissions'
            ]
        }

        response = self.post(education_group_year.academic_year.year,
                             language,
                             education_group_year.acronym,
                             data=message)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response_json = response.json()

        useless, condition_admissions_section = remove_conditions_admission(response_json['sections'])
        sections = condition_admissions_section['content']['sections']
        self.assertEqual(sections['university_bachelors']['text'], admission_condition.text_university_bachelors)
        self.assertEqual(sections['personalized_access']['text-common'],
                         admission_condition_common.text_personalized_access)
        self.assertEqual(sections['adults_taking_up_university_training']['text-common'],
                         admission_condition_common.text_adults_taking_up_university_training)
        self.assertEqual(sections['admission_enrollment_procedures']['text-common'],
                         admission_condition_common.text_admission_enrollment_procedures)

    def test_admission_conditions_for_master_with_diplomas(self):
        education_group_year = EducationGroupYearFactory(acronym='actu2m')

        admission_condition = AdmissionCondition.objects.create(education_group_year=education_group_year)

        education_group_year_common = EducationGroupYearFactory(acronym='common-2m',
                                                                academic_year=education_group_year.academic_year)
        acl = AdmissionConditionLine.objects.create(admission_condition=admission_condition)
        acl.section = 'ucl_bachelors'
        acl.diploma = 'diploma'
        acl.conditions = 'conditions'
        acl.remarks = 'remarks'
        acl.access = 'access'
        acl.save()

        iso_language, language = 'fr-be', 'fr'

        message = {
            'anac': education_group_year.academic_year.year,
            'code_offre': education_group_year.acronym,
            'sections': [
                'conditions_admissions'
            ]
        }

        response = self.post(education_group_year.academic_year.year,
                             language,
                             education_group_year.acronym,
                             data=message)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')

        response_json = response.json()

        useless, condition_admissions_section = remove_conditions_admission(response_json['sections'])
        sections = condition_admissions_section['content']['sections']
        self.assertEqual(len(sections['university_bachelors']['records']['ucl_bachelors']), 1)
