##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.db.models import OuterRef, F, Subquery, fields
from django.urls import reverse

from base.business.education_groups import general_information_sections
from base.models.education_group_achievement import EducationGroupAchievement
from cms.enums import entity_name
from cms.models import translated_text
from cms.models.text_label import TextLabel
from cms.models.translated_text import TranslatedText
from cms.models.translated_text_label import TranslatedTextLabel
from program_management.ddd.domain.node import NodeGroupYear
from education_group.views.proxy.read import Tab


def get_achievements(node: NodeGroupYear, path: str):
    qs = EducationGroupAchievement.objects.filter(
        education_group_year__educationgroupversion__root_group__partial_acronym=node.code,
        education_group_year__educationgroupversion__root_group__academic_year__year=node.year
    ).prefetch_related('educationgroupdetailedachievement_set')

    achievements = []
    for achievement in qs:
        achievements.append({
            **__get_achievement_formated(achievement, node, path),
            'detailed_achievements': [
                __get_detail_achievement_formated(achievement, d_achievement, node, path) for d_achievement
                in achievement.educationgroupdetailedachievement_set.all()
            ]
        })
    return achievements


def __get_achievement_formated(achievement, node, path):
    url_names = _get_url_name_achievements(achievement)
    return {
        'pk': achievement.pk,
        'code_name': achievement.code_name,
        'text_fr': achievement.french_text,
        'text_en': achievement.english_text,
        'url_action': reverse(
            url_names["url_action"],
            args=[node.year, node.code, achievement.pk]
        ) + '?path={}&tab={}'.format(path, Tab.SKILLS_ACHIEVEMENTS),
        'url_update': reverse(
            url_names["url_update"], args=[node.year, node.code, achievement.pk]
        ) + '?path={}&tab={}#achievement_{}'.format(path, Tab.SKILLS_ACHIEVEMENTS, achievement.pk),
        'url_delete': reverse(
            url_names["url_delete"], args=[node.year, node.code, achievement.pk]
        ) + '?path={}&tab={}'.format(path, Tab.SKILLS_ACHIEVEMENTS),
        'url_create': reverse(
            url_names["url_create"], args=[node.year, node.code, achievement.pk]
        ) + '?path={}&tab={}achievement.pk'.format(path, Tab.SKILLS_ACHIEVEMENTS, achievement.pk)
    }


def _get_url_name_achievements(achievement):
    prefix = 'training_' if achievement.education_group_year.is_training() else 'minitraining_'
    return {
        'url_action': prefix+"achievement_actions",
        'url_update': prefix+"achievement_update",
        'url_delete': prefix+"achievement_delete",
        'url_create': prefix+"detailed_achievement_create"
    }


def __get_detail_achievement_formated(achievement, d_achievement, node, path):
    url_names = _get_url_name_detail_achievements(achievement)
    return {
        'pk': d_achievement.pk,
        'code_name': d_achievement.code_name,
        'text_fr': d_achievement.french_text,
        'text_en': d_achievement.english_text,
        'url_action': reverse(
            url_names["url_action"],
            args=[node.year, node.code, achievement.pk, d_achievement.pk]
        ) + '?path={}&tab={}'.format(path, Tab.SKILLS_ACHIEVEMENTS),
        'url_update': reverse(
            url_names["url_update"], args=[node.year, node.code, achievement.pk, d_achievement.pk]
        ) + '?path={}&tab={}#detail_achievements_{}'.format(path, Tab.SKILLS_ACHIEVEMENTS, d_achievement.pk),
        'url_delete': reverse(
            url_names["url_delete"], args=[node.year, node.code, achievement.pk, d_achievement.pk]
        ) + '?path={}&tab={}#achievement_{}'.format(path, Tab.SKILLS_ACHIEVEMENTS, achievement.pk),
    }


def _get_url_name_detail_achievements(achievement):
    prefix = 'training_' if achievement.education_group_year.is_training() else 'minitraining_'
    return {
        'url_action': prefix+"detailed_achievement_actions",
        'url_update': prefix+"detailed_achievement_update",
        'url_delete': prefix+"detailed_achievement_delete",
    }


def get_skills_labels(node: NodeGroupYear, language_code: str):
    reference_pk = translated_text.get_groups_or_offers_cms_reference_object(node).pk
    subqstranslated_fr = TranslatedText.objects.filter(
        reference=reference_pk, text_label=OuterRef('pk'),
        language=settings.LANGUAGE_CODE_FR, entity=entity_name.OFFER_YEAR
    ).values('text')[:1]
    subqstranslated_en = TranslatedText.objects.filter(
        reference=reference_pk, text_label=OuterRef('pk'),
        language=settings.LANGUAGE_CODE_EN, entity=entity_name.OFFER_YEAR
    ).values('text')[:1]
    subqslabel = TranslatedTextLabel.objects.filter(
        text_label=OuterRef('pk'),
        language=language_code
    ).values('label')[:1]

    label_ids = [
        general_information_sections.CMS_LABEL_PROGRAM_AIM,
        general_information_sections.CMS_LABEL_ADDITIONAL_INFORMATION
    ]

    qs = TextLabel.objects.filter(
        label__in=label_ids,
        entity=entity_name.OFFER_YEAR
    ).annotate(
        label_id=F('label'),
        label_translated=Subquery(subqslabel, output_field=fields.CharField()),
        text_fr=Subquery(subqstranslated_fr, output_field=fields.CharField()),
        text_en=Subquery(subqstranslated_en, output_field=fields.CharField())
    ).values('label_id', 'label_translated', 'text_fr', 'text_en')

    labels_translated = []
    for label_id in label_ids:
        try:
            labels_translated.append(next(label for label in qs if label['label_id'] == label_id))
        except StopIteration:
            # Default value if not found on database
            labels_translated.append({'label_id': label_id, 'label_translated': '', 'text_fr': '', 'text_en': ''})
    return labels_translated
