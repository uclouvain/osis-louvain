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
from django.db.models import Prefetch, CharField, Case, When, Value
from django.db.models.functions import Lower

from base.models.education_group_achievement import EducationGroupAchievement
from base.models.education_group_detailed_achievement import EducationGroupDetailedAchievement
from base.models.education_group_publication_contact import EducationGroupPublicationContact
from base.models.education_group_year import EducationGroupYear
from base.models.enums.publication_contact_type import PublicationContactType
from base.models.utils.utils import get_object_or_none
from cms.enums import entity_name
from cms.enums.entity_name import OFFER_YEAR
from cms.models.translated_text import TranslatedText

SKILLS_AND_ACHIEVEMENTS_KEY = 'comp_acquis'
SKILLS_AND_ACHIEVEMENTS_AA_DATA = 'achievements'
SKILLS_AND_ACHIEVEMENTS_CMS_DATA = ('skills_and_achievements_introduction', 'skills_and_achievements_additional_text',)

EVALUATION_KEY = 'evaluation'
CONTACTS_KEY = 'contacts'
CONTACT_INTRO_KEY = 'contact_intro'


def get_achievements(education_group_year, language_code):
    if language_code in [settings.LANGUAGE_CODE_FR, settings.LANGUAGE_CODE_EN]:
        qs = EducationGroupAchievement.objects.filter(
            education_group_year=education_group_year
        ).prefetch_related(
            Prefetch(
                'educationgroupdetailedachievement_set',
                queryset=EducationGroupDetailedAchievement.objects.all().annotate_text(language_code),
                to_attr='detailed_achievements',
            ),
        ).annotate_text(language_code)\


        achievement_list = []
        for education_group_achievement in qs:
            row = {
                'teaser': education_group_achievement.text,
                'detailed_achievements':
                    _get_detailed_achievements(education_group_achievement.detailed_achievements) or None,
                'code_name': _clean_code_name(education_group_achievement.code_name)
            }
            achievement_list.append(row)
        return achievement_list
    raise AttributeError('Language code not supported {}'.format(language_code))


def _get_detailed_achievements(education_group_detailed_achievements):
    return [
        {'code_name': _clean_code_name(detailed_achievement.code_name), 'text': detailed_achievement.text}
        for detailed_achievement in education_group_detailed_achievements
    ]


# FIX ME: remove this line when user have clean DB
def _clean_code_name(code_name):
    if code_name == '.':
        return None
    return code_name


def get_intro_extra_content_achievements(education_group_year, language_code):
    qs = TranslatedText.objects.filter(
        entity=entity_name.OFFER_YEAR,
        reference=education_group_year.id,
        language=language_code,
        text_label__label__in=SKILLS_AND_ACHIEVEMENTS_CMS_DATA
    ).select_related('text_label')
    return {cms_data.text_label.label: cms_data.text for cms_data in qs}


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


def get_common_evaluation_text(education_group_year, language_code):
    common_education_group_year = EducationGroupYear.objects.get_common(
        academic_year=education_group_year.academic_year,
    )

    translated_text = TranslatedText.objects.get(
        text_label__entity=OFFER_YEAR,
        text_label__label=EVALUATION_KEY,
        language=language_code,
        entity=OFFER_YEAR,
        reference=common_education_group_year.id
    )

    return translated_text.text


def get_contacts_group_by_types(education_group_year, language_code):
    qs = EducationGroupPublicationContact.objects.filter(
        education_group_year=education_group_year
    ).annotate_text(language_code)\
     .annotate(
        # Business rules: Empty str must be converted to null
        role_value=Case(
            When(role_text__exact='', then=None),
            default='role_text',
            output_field=CharField()
        ),
        email_value=Case(
            When(email__exact='', then=None),
            default='email',
            output_field=CharField()
        ),
        description_value=Case(
            When(description__exact='', then=None),
            default='description',
            output_field=CharField()
        ),
        type_value=Case(
            When(
                type=PublicationContactType.ACADEMIC_RESPONSIBLE.name,
                then=Value('academic_responsibles')
            ),
            When(
                type=PublicationContactType.OTHER_ACADEMIC_RESPONSIBLE.name,
                then=Value('other_academic_responsibles'),
            ),
            When(
                type=PublicationContactType.JURY_MEMBER.name,
                then=Value('jury_members'),
            ),
            When(
                type=PublicationContactType.OTHER_CONTACT.name,
                then=Value('other_contacts'),
            ),
            default=Lower('type'),
            output_field=CharField()
        )
     ).values('role_value', 'email_value', 'description_value', 'type_value')

    contacts = {}
    for contact in qs:
        row = {
            'role': contact['role_value'],
            'email': contact['email_value'],
            'description': contact['description_value']
        }
        contacts.setdefault(contact['type_value'], []).append(row)
    return contacts


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
