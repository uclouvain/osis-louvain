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

from base.tests.factories.education_group_achievement import EducationGroupAchievementFactory
from base.tests.factories.education_group_detailed_achievement import EducationGroupDetailedAchievementFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from cms.enums.entity_name import OFFER_YEAR
from cms.tests.factories.translated_text import TranslatedTextFactory
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from webservices.api.serializers.achievement import AchievementSerializer, AchievementsSerializer, \
    DetailedAchievementSerializer
from webservices.business import SKILLS_AND_ACHIEVEMENTS_INTRO, SKILLS_AND_ACHIEVEMENTS_EXTRA


class AchievementsSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.language = settings.LANGUAGE_CODE_EN
        cls.egy = EducationGroupYearFactory()
        for label in [SKILLS_AND_ACHIEVEMENTS_INTRO, SKILLS_AND_ACHIEVEMENTS_EXTRA]:
            TranslatedTextFactory(
                text_label__label=label,
                reference=cls.egy.id,
                entity=OFFER_YEAR,
                language=cls.language
            )
        cls.node = NodeGroupYearFactory(node_id=cls.egy.id)
        cls.serializer = AchievementsSerializer(cls.node, context={'language': cls.language, 'offer': cls.egy})

    def test_contains_expected_fields(self):
        expected_fields = [
            'intro',
            'blocs',
            'extra'
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)


class AchievementSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.achievement = EducationGroupAchievementFactory()
        cls.serializer = AchievementSerializer(cls.achievement)

    def test_contains_expected_fields(self):
        expected_fields = [
            'teaser',
            'detailed_achievements',
            'code_name'
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)


class DetailedAchievementSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.achievement = EducationGroupDetailedAchievementFactory()
        cls.serializer = DetailedAchievementSerializer(cls.achievement)

    def test_contains_expected_fields(self):
        expected_fields = [
            'code_name',
            'text',
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)
