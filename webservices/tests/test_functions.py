import unittest

from django.http import Http404
from django.test import TestCase

from base.tests.factories.education_group_year import EducationGroupYearFactory
from webservices.views import get_title_of_education_group_year, to_int_or_404


class GetTitleOrEducationGroupYear_TestCase(TestCase):
    def test_get_title_or_education_group_year(self):
        ega = EducationGroupYearFactory(title='french', title_english='english')

        title = get_title_of_education_group_year(ega, 'fr-be')
        self.assertEqual('french', title)

        title = get_title_of_education_group_year(ega, 'en')
        self.assertEqual('english', title)


class UtilsTestCase(unittest.TestCase):
    def test_with_404(self):
        with self.assertRaises(Http404):
            to_int_or_404('salut')

    def test_no_404(self):
        result = to_int_or_404('10')
        self.assertEqual(result, 10)