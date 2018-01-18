from unittest import TestCase
from django.core.exceptions import ObjectDoesNotExist
from reference.models import country as mdl_country
from reference.tests.factories import country


class TestCountry(TestCase):
    def test_find_by_iso_code(self):
        a_country = country.CountryFactory()
        found_country = mdl_country.get_by_iso_code(a_country.iso_code)
        self.assertEquals(a_country, found_country)

    def test_inexisting_iso_code(self):
        a_country = mdl_country.get_by_iso_code("")
        self.assertIsNone(a_country)
