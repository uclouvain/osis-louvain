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

from base.business.education_groups import general_information_sections
from base.models.education_group_achievement import EducationGroupAchievement
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import GroupType
from cms.models.text_label import TextLabel
from cms.models.translated_text import TranslatedText
from cms.models.translated_text_label import TranslatedTextLabel
from education_group.models.group_year import GroupYear
from program_management.ddd.domain.node import NodeGroupYear


def get_achievements(node: NodeGroupYear):
    qs = EducationGroupAchievement.objects.filter(
        education_group_year__educationgroupversion__root_group__partial_acronym=node.code,
        education_group_year__educationgroupversion__root_group__academic_year__year=node.year
    ).prefetch_related('educationgroupdetailedachievement_set')

    achievements = []
    for achievement in qs:
        achievements.append({
            **__get_achievement_formated(achievement),
            'detailed_achievements': [
                __get_achievement_formated(d_achievement) for d_achievement
                in achievement.educationgroupdetailedachievement_set.all()
            ]
        })
    return achievements


def __get_achievement_formated(achievement):
    return {
        'pk': achievement.pk,
        'code_name': achievement.code_name,
        'text_fr': achievement.french_text,
        'text_en': achievement.english_text
    }


def get_skills_labels(node: NodeGroupYear, language_code: str):
    reference_pk = __get_reference_pk(node)
    subqstranslated_fr = TranslatedText.objects.filter(reference=reference_pk, text_label=OuterRef('pk'),
                                                       language=settings.LANGUAGE_CODE_FR).values('text')[:1]
    subqstranslated_en = TranslatedText.objects.filter(reference=reference_pk, text_label=OuterRef('pk'),
                                                       language=settings.LANGUAGE_CODE_EN).values('text')[:1]
    subqslabel = TranslatedTextLabel.objects.filter(
        text_label=OuterRef('pk'),
        language=language_code
    ).values('label')[:1]

    label_ids = [
        general_information_sections.CMS_LABEL_PROGRAM_AIM,
        general_information_sections.CMS_LABEL_ADDITIONAL_INFORMATION
    ]

    qs = TextLabel.objects.filter(
        label__in=label_ids
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


def __get_reference_pk(node: NodeGroupYear):
    if node.category.name in GroupType.get_names():
        return GroupYear.objects.get(element__pk=node.pk).pk
    else:
        return EducationGroupYear.objects.get(educationgroupversion__root_group__element__pk=node.pk).pk
