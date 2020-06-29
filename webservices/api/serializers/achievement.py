##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2018 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db.models import Case, When, CharField, F
from rest_framework import serializers

from base.models.education_group_achievement import EducationGroupAchievement
from base.models.education_group_detailed_achievement import EducationGroupDetailedAchievement
from cms.enums import entity_name
from cms.models.translated_text import TranslatedText
from webservices.business import SKILLS_AND_ACHIEVEMENTS_INTRO, SKILLS_AND_ACHIEVEMENTS_EXTRA


class DetailedAchievementSerializer(serializers.ModelSerializer):
    code_name = serializers.SerializerMethodField()
    text = serializers.SerializerMethodField()

    class Meta:
        model = EducationGroupDetailedAchievement

        fields = (
            'code_name',
            'text',
        )

    def get_text(self, obj):
        return _get_appropriate_text(obj, self.context)

    @staticmethod
    def get_code_name(obj):
        return _get_appropriate_code_name(obj)


class AchievementSerializer(serializers.ModelSerializer):
    code_name = serializers.SerializerMethodField()
    teaser = serializers.SerializerMethodField(source='text')
    detailed_achievements = DetailedAchievementSerializer(
        source='educationgroupdetailedachievement_set',
        read_only=True,
        many=True
    )

    class Meta:
        model = EducationGroupAchievement

        fields = (
            'teaser',
            'detailed_achievements',
            'code_name'
        )

    def get_teaser(self, obj):
        return _get_appropriate_text(obj, self.context)

    @staticmethod
    def get_code_name(obj):
        return _get_appropriate_code_name(obj)


class AchievementsSerializer(serializers.Serializer):
    intro = serializers.SerializerMethodField()
    blocs = serializers.SerializerMethodField()
    extra = serializers.SerializerMethodField()

    def get_blocs(self, obj):
        offer = self.context.get('offer')
        qs = offer.educationgroupachievement_set.all()
        return AchievementSerializer(qs, many=True).data

    def get_intro(self, obj):
        return self._get_cms_achievement_data(SKILLS_AND_ACHIEVEMENTS_INTRO)

    def get_extra(self, obj):
        return self._get_cms_achievement_data(SKILLS_AND_ACHIEVEMENTS_EXTRA)

    def _get_cms_achievement_data(self, cms_type):
        offer = self.context.get('offer')
        try:
            data = TranslatedText.objects.select_related(
                'text_label'
            ).annotate(
                text_or_none=Case(
                    When(text__exact='', then=None),
                    default=F('text'),
                    output_field=CharField()
                )
            ).get(
                entity=entity_name.OFFER_YEAR,
                language=self.context['language'],
                text_label__label=cms_type,
                reference=offer.id
            )
            return data.text_or_none
        except TranslatedText.DoesNotExist:
            return None


def _get_appropriate_text(eg_achievement, context):
    if context.get('language') == settings.LANGUAGE_CODE_EN:
        return eg_achievement.english_text
    return eg_achievement.french_text


def _get_appropriate_code_name(eg_achievement):
    return eg_achievement.code_name if eg_achievement.code_name != '.' else None
