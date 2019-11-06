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
from django.test import TestCase

from cms.enums import entity_name
from cms.models.translated_text import TranslatedText
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory

REFERENCE = 2502


class TranslatedTextTest(TestCase):

    def test_find_by_entity_reference(self):
        text_label_lu_3 = TextLabelFactory(order=1, label='program', entity=entity_name.LEARNING_UNIT_YEAR)
        text_label_oy_1 = TextLabelFactory(order=2, label='introduction', entity=entity_name.OFFER_YEAR)
        text_label_oy_2 = TextLabelFactory(order=3, label='profil', entity=entity_name.OFFER_YEAR)
        text_label_oy_3 = TextLabelFactory(order=4, label='job', entity=entity_name.OFFER_YEAR)

        TranslatedTextFactory(text_label=text_label_lu_3,
                              entity=entity_name.LEARNING_UNIT_YEAR,
                              reference=REFERENCE)

        TranslatedTextFactory(text_label=text_label_oy_1,
                              entity=entity_name.OFFER_YEAR,
                              reference=REFERENCE)
        TranslatedTextFactory(text_label=text_label_oy_2,
                              entity=entity_name.OFFER_YEAR,
                              reference=REFERENCE)
        TranslatedTextFactory(text_label=text_label_oy_3,
                              entity=entity_name.OFFER_YEAR,
                              reference=REFERENCE)

        tt = TranslatedText.objects.filter(
            text_label__entity=entity_name.OFFER_YEAR,
            reference=REFERENCE
        ).order_by('text_label__order').values_list('text_label__label', flat=True)
        self.assertEqual(
            list(tt),
            [text_label_oy_1.label, text_label_oy_2.label, text_label_oy_3.label]
        )
