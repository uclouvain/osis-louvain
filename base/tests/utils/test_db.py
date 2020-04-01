from django.db.models import F
from django.test import SimpleTestCase

import base.utils.db


class TestConvertOrderByStringsToExpressions(SimpleTestCase):
    def test_when_no_string(self):
        result = base.utils.db.convert_order_by_strings_to_expressions(tuple())
        self.assertEqual(result, tuple())

    def test_when_one_field(self):
        result = base.utils.db.convert_order_by_strings_to_expressions(
            ("acronym", )
        )
        self.assertEqual(
            result,
            (F("acronym"), )
        )

    def test_when_multiple_fields(self):
        result = base.utils.db.convert_order_by_strings_to_expressions(
            ("acronym", "academic_year", "title")
        )
        self.assertEqual(
            result,
            (F("acronym"), F("academic_year"), F("title"))
        )

    def test_when_reverse_order(self):
        result = base.utils.db.convert_order_by_strings_to_expressions(
            ("acronym", "-academic_year", "title")
        )
        self.assertEqual(
            result,
            (F("acronym"), F("academic_year").desc(), F("title"))
        )