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
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Value, CharField
from rest_framework import serializers

from base.business.education_groups import group_element_year_tree
from base.business.education_groups.general_information_sections import SECTIONS_PER_OFFER_TYPE, \
    SKILLS_AND_ACHIEVEMENTS, ADMISSION_CONDITION, CONTACTS, CONTACT_INTRO, INTRODUCTION
from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import GroupType
from base.models.group_element_year import GroupElementYear
from cms.enums.entity_name import OFFER_YEAR
from cms.models.translated_text import TranslatedText
from cms.models.translated_text_label import TranslatedTextLabel
from webservices.api.serializers.section import SectionSerializer, AchievementSectionSerializer, \
    AdmissionConditionSectionSerializer, ContactsSectionSerializer
from webservices.business import EVALUATION_KEY, get_evaluation_text


class GeneralInformationSerializer(serializers.ModelSerializer):
    language = serializers.CharField(read_only=True)
    year = serializers.IntegerField(source='academic_year.year', read_only=True)
    sections = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = EducationGroupYear

        fields = (
            'language',
            'acronym',
            'title',
            'year',
            'sections'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lang = kwargs['context']['language']
        self.instance.language = lang
        if lang != settings.LANGUAGE_CODE_FR[:2]:
            self.fields['title'] = serializers.CharField(source='title_english', read_only=True)

    def get_sections(self, obj):
        datas = []
        sections = []
        language = settings.LANGUAGE_CODE_FR \
            if self.instance.language == settings.LANGUAGE_CODE_FR[:2] else self.instance.language
        pertinent_sections = SECTIONS_PER_OFFER_TYPE[obj.education_group_type.name]
        common_egy = EducationGroupYear.objects.get_common(
            academic_year=obj.academic_year
        )
        cms_serializers = {
            SKILLS_AND_ACHIEVEMENTS: AchievementSectionSerializer,
            ADMISSION_CONDITION: AdmissionConditionSectionSerializer,
            CONTACTS: ContactsSectionSerializer
        }
        extra_intro_offers = self._get_intro_offers(obj)

        for common_section in pertinent_sections['common']:
            sections.append(self._get_translated_text(common_egy, common_section, language))

        for specific_section in pertinent_sections['specific']:
            serializer = cms_serializers.get(specific_section)
            if serializer:
                serializer = serializer({'id': specific_section}, context={'egy': obj, 'lang': language})
                datas.append(serializer.data)
            elif specific_section not in [EVALUATION_KEY, CONTACT_INTRO]:
                sections.append(self._get_translated_text(obj, specific_section, language))

        for offer in extra_intro_offers:
            sections.append(self._get_translated_text(offer, 'intro', language))

        datas += SectionSerializer(sections, many=True).data
        return datas

    def _get_translated_text(self, egy, section, language):
        translated_text_label = TranslatedTextLabel.objects.get(
            text_label__label=section,
            language=language,
        )
        translated_text = TranslatedText.objects.filter(
            text_label__label=section,
            language=language,
            entity=OFFER_YEAR,
            reference=egy.id
        ).annotate(
            label=Value(
                self._get_correct_label_name(egy, section),
                output_field=CharField()
            ),
            translated_label=Value(translated_text_label.label, output_field=CharField())
        )

        if section == EVALUATION_KEY:
            return self._get_evaluation_text(language, translated_text)

        try:
            return translated_text.values('label', 'translated_label', 'text').get()
        except ObjectDoesNotExist:
            return {
                'label': self._get_correct_label_name(egy, section),
                'translated_label': translated_text_label.label,
                'text': None
            }

    @staticmethod
    def _get_correct_label_name(egy, section):
        if section == INTRODUCTION:
            return 'intro-' + egy.partial_acronym.lower()
        elif 'common' in egy.acronym and section != EVALUATION_KEY:
            return section + '-commun'
        return section

    def _get_evaluation_text(self, language, translated_text):
        try:
            _, text = get_evaluation_text(self.instance, language)
        except TranslatedText.DoesNotExist:
            text = None
        translated_text = translated_text.annotate(
            free_text=Value(text, output_field=CharField())
        ).values(
            'label', 'translated_label', 'text', 'free_text'
        ).first()
        return translated_text

    @staticmethod
    def _get_intro_offers(obj):
        hierarchy = group_element_year_tree.EducationGroupHierarchy(root=obj)
        extra_intro_offers = hierarchy.get_finality_list() + hierarchy.get_option_list()
        common_core = GroupElementYear.objects.select_related('child_branch').filter(
            parent=obj,
            child_branch__education_group_type__name=GroupType.COMMON_CORE.name
        ).first()
        if common_core:
            extra_intro_offers.append(common_core.child_branch)
        return extra_intro_offers
