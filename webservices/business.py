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
from django.db.models import Prefetch

from cms.enums.entity_name import OFFER_YEAR
from cms.models.translated_text import TranslatedText
from osis_common.utils.models import get_object_or_none

SKILLS_AND_ACHIEVEMENTS_INTRO = 'skills_and_achievements_introduction'
SKILLS_AND_ACHIEVEMENTS_EXTRA = 'skills_and_achievements_additional_text'

EVALUATION_KEY = 'evaluation'
CONTACT_INTRO_KEY = 'contact_intro'
UNIVERSITY_TYPES = ['bachelors_dutch', 'foreign_bachelors', 'others_bachelors_french', 'ucl_bachelors']
SECOND_DEGREE_TYPES = ['masters', 'graduates']
ADMISSION_CONDITION_LINE_FIELDS = [
    ('university_bachelors', UNIVERSITY_TYPES),
    ('holders_second_university_degree', SECOND_DEGREE_TYPES)
]
ADMISSION_CONDITION_FIELDS = [
    'admission_enrollment_procedures',
    'non_university_bachelors',
    'holders_non_university_second_degree',
    'adults_taking_up_university_training',
    'personalized_access',
]


def get_evaluation_text(education_group_year, language_code):
    translated_text = TranslatedText.objects.all().prefetch_related(
        Prefetch(
            'text_label__translatedtextlabel_set',
            to_attr="translated_text_labels"
        )
    ).get(
        text_label__entity=OFFER_YEAR,
        text_label__label=EVALUATION_KEY,
        language=language_code,
        entity=OFFER_YEAR,
        reference=education_group_year.id
    )
    translated_text_label = next(
        (
            text_label.label for text_label in translated_text.text_label.translated_text_labels
            if text_label.language == language_code
        ),
        EVALUATION_KEY
    )

    return translated_text_label, translated_text.text


def get_contacts_intro_text(education_group_year, language_code):
    introduction = get_object_or_none(
        TranslatedText,
        text_label__entity=OFFER_YEAR,
        text_label__label=CONTACT_INTRO_KEY,
        language=language_code,
        entity=OFFER_YEAR,
        reference=education_group_year.id
    )
    if introduction:
        return introduction.text
    return None
