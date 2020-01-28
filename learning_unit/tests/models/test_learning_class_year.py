from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils.translation import gettext_lazy as _

from base.tests.factories.learning_component_year import LearningComponentYearFactory
from learning_unit.tests.factories.learning_class_year import LearningClassYearFactory


class LearningClassYearTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.learning_class_year = LearningClassYearFactory(learning_component_year=LearningComponentYearFactory())

    def test_learning_class_year_str(self):
        expected_string = u'{}-{}'.format(
            self.learning_class_year.learning_component_year.acronym,
            self.learning_class_year.acronym
        )
        self.assertEqual(str(self.learning_class_year), expected_string)

    def test_acronym_should_contains_only_letters(self):
        self.learning_class_year.acronym = '123'
        with self.assertRaises(ValidationError) as cm:
            self.learning_class_year.full_clean()
        self.assertTrue('acronym' in cm.exception.message_dict.keys())
        self.assertEqual(cm.exception.message_dict['acronym'][0], _('Only letters are allowed.'))
