import factory

from reference.tests.factories.language import LanguageFactory
from testing.providers import LANGUAGES


class ReferenceDataGenerator:
    def __init__(self):
        self.languages = LanguageFactory.create_batch(
            len(LANGUAGES),
            _language=factory.Iterator(LANGUAGES)
        )
