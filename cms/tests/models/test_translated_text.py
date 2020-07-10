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

from cms.models.translated_text import TranslatedText
from cms.tests.factories.text_label import OfferTextLabelFactory, GroupTextLabelFactory, \
    LearningUnitYearTextLabelFactory
from cms.tests.factories.translated_text import OfferTranslatedTextFactory, \
    LearningUnitYearTranslatedTextFactory, GroupTranslatedTextFactory

REFERENCE = 2502


class TranslatedTextTest(TestCase):
    def test_find_by_entity_reference(self):
        text_label_lu_3 = LearningUnitYearTextLabelFactory(order=1, label='program')
        text_label_oy_1 = OfferTextLabelFactory(order=2, label='introduction')
        text_label_oy_2 = OfferTextLabelFactory(order=3, label='profil')
        text_label_oy_3 = OfferTextLabelFactory(order=4, label='job')
        text_label_gy_1 = GroupTextLabelFactory(order=5, label='test')

        LearningUnitYearTranslatedTextFactory(text_label=text_label_lu_3,
                                              reference=REFERENCE)

        OfferTranslatedTextFactory(text_label=text_label_oy_1,
                                   reference=REFERENCE)
        OfferTranslatedTextFactory(text_label=text_label_oy_2,
                                   reference=REFERENCE)
        OfferTranslatedTextFactory(text_label=text_label_oy_3,
                                   reference=REFERENCE)
        GroupTranslatedTextFactory(text_label=text_label_gy_1,
                                   reference=REFERENCE)

        tt = TranslatedText.objects.filter(
            reference=REFERENCE,
            entity='offer_year'
        ).order_by('text_label__order').values_list('text_label__label', flat=True)
        self.assertEqual(
            list(tt),
            [text_label_oy_1.label, text_label_oy_2.label, text_label_oy_3.label]
        )
