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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.conf import settings
from django.test import TestCase

from cms.enums import entity_name
from cms.models.translated_text_label import get_label_translation
from cms.tests.factories.text_label import OfferTextLabelFactory
from cms.tests.factories.translated_text_label import TranslatedTextLabelFactory


class TranslatedTextLabelTest(TestCase):
    def test_get_label_translation(self):
        text_label = OfferTextLabelFactory(
            label='TEST_LABEL'
        )
        TranslatedTextLabelFactory(
            language=settings.LANGUAGE_CODE_FR,
            text_label=text_label,
            label='TEST_LABEL_TRANSLATED'
        )
        self.assertEqual(
            get_label_translation(
                text_entity=entity_name.OFFER_YEAR,
                label='TEST_LABEL',
                language=settings.LANGUAGE_CODE_FR
            ),
            'TEST_LABEL_TRANSLATED'
        )
