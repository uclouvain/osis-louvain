import json

from django.test import TestCase
# Create your tests here.

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from cms.enums.entity_name import OFFER_YEAR
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory
from cms.tests.factories.translated_text_label import TranslatedTextLabelFactory
from webservices.tests.helper import Helper


class CatalogOfferWebServiceTestCase(TestCase, Helper):
    URL_NAME = 'v0.1-ws_catalog_offer'

    def test_year_not_found(self):
        response = self._get_response(1990, 'fr', 'actu2m')
        self.assertEqual(response.status_code, 404)

    def test_language_not_found(self):
        response = self._get_response(2017, 'ch', 'actu2m')
        self.assertEqual(response.status_code, 404)

    def test_acronym_not_found(self):
        response = self._get_response(2017, 'fr', 'XYZ')
        self.assertEqual(response.status_code, 404)

    def test_basic_education_group_year(self):
        academic_year = AcademicYearFactory()
        education_group_year = EducationGroupYearFactory(academic_year=academic_year)

        response = self._get_response(academic_year.year, 'fr', education_group_year.acronym)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        response_json = json.loads(response.content.decode('utf-8'))

        self.assertDictEqual(response_json, {
            'acronym': education_group_year.acronym,
            'title': education_group_year.title,
            'year': academic_year.year,
            'language': 'fr',
            'sections': []
        })

    def _test_education_group_year_with_translation(self, language, iso_language):
        values = self._create_records_for_test_education_group_year(iso_language)

        academic_year, education_group_year, text_label, translated_text, translated_text_label = values

        response = self._get_response(academic_year.year, language, education_group_year.acronym)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        response_json = json.loads(response.content.decode('utf-8'))

        context = {
            'academic_year': academic_year,
            'education_group_year': education_group_year,
            'language': language,
            'text_label': text_label,
            'translated_text': translated_text,
            'translated_text_label': translated_text_label
        }

        fake_response = self._mock_response_dictionary(**context)
        self.assertDictEqual(response_json, fake_response)

    def _create_records_for_test_education_group_year(self, iso_language):
        academic_year = AcademicYearFactory()
        education_group_year = EducationGroupYearFactory(academic_year=academic_year)
        text_label = TextLabelFactory(entity=OFFER_YEAR)
        translated_text_label = TranslatedTextLabelFactory(language=iso_language,
                                                           text_label=text_label)
        translated_text = TranslatedTextFactory(
            text_label=text_label,
            entity=text_label.entity,
            reference=education_group_year.id,
            language=iso_language,
            # text is randomized
        )
        return academic_year, education_group_year, text_label, translated_text, translated_text_label

    def _mock_response_dictionary(self, **kwargs):
        return {
            'acronym': kwargs['education_group_year'].acronym,
            'title': kwargs['education_group_year'].title_english,
            'year': kwargs['academic_year'].year,
            'language': kwargs['language'],
            'sections': [
                {
                    'content': kwargs['translated_text'].text,
                    'label': kwargs['translated_text_label'].label,
                    'id': kwargs['text_label'].label
                }
            ]
        }

    def test_education_group_year_with_translation_fr(self):
        self._test_education_group_year_with_translation('fr', 'fr-be')

    def test_education_group_year_with_translation_en(self):
        self._test_education_group_year_with_translation('en', 'en')
