import json

from django.test import TestCase

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from webservices.tests.helper import Helper


class CatalogGroupWebServiceTestCase(TestCase, Helper):
    URL_NAME = 'v0.1-ws_catalog_group'

    def test_year_not_found(self):
        response = self._get_response(1990, 'fr', 'actu2m')
        self.assertEqual(response.status_code, 404)

    def test_language_not_found(self):
        response = self._get_response(2017, 'ch', 'actu2m')
        self.assertEqual(response.status_code, 404)

    def test_acronym_not_found(self):
        response = self._get_response(2017, 'fr', 'XYZ')
        self.assertEqual(response.status_code, 404)


    def test_basic_education_group_year_group(self):
        academic_year = AcademicYearFactory()
        education_group_year = EducationGroupYearFactory(academic_year=academic_year)

        response = self._get_response(academic_year.year, 'fr',
                                      education_group_year.partial_acronym)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, 'application/json')
        response_json = json.loads(response.content.decode('utf-8'))

        self.assertDictEqual(response_json, {
            'acronym': education_group_year.acronym,
            'partial_acronym': education_group_year.partial_acronym,
            'title': education_group_year.title,
            'year': academic_year.year,
            'language': 'fr',
            'sections': []
        })