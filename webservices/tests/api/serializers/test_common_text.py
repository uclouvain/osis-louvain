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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

from django.conf import settings
from django.test import TestCase

from base.business.education_groups import general_information_sections
from base.tests.factories.education_group_year import EducationGroupYearCommonFactory
from cms.enums.entity_name import OFFER_YEAR
from cms.tests.factories.translated_text import TranslatedTextFactory
from webservices.api.serializers.common_text import CommonTextSerializer


class CommonTextSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.language = settings.LANGUAGE_CODE_EN
        cls.egy = EducationGroupYearCommonFactory()
        cls.pertinent_sections = general_information_sections.SECTIONS_PER_OFFER_TYPE['common']
        cls.data = {}
        for section in cls.pertinent_sections['specific']:
            tt = TranslatedTextFactory(
                reference=cls.egy.id,
                entity=OFFER_YEAR,
                language=cls.language,
                text_label__label=section
            )
            cls.data[tt.text_label.label] = tt.text

        cls.serializer = CommonTextSerializer(cls.data, context={'language': cls.language})

    def test_contains_expected_fields(self):
        expected_fields = [
            'agregation',
            'caap',
            'prerequis',
            'module_complementaire',
            'evaluation',
            'finalites_didactiques-commun'
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)
