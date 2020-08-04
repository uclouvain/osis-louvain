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

from base.business.education_groups import general_information_sections
from base.business.education_groups.general_information_sections import \
    SKILLS_AND_ACHIEVEMENTS, ADMISSION_CONDITION, CONTACTS, CONTACT_INTRO, INTRODUCTION
from base.models.enums.education_group_types import GroupType
from cms.enums import entity_name
from cms.models import translated_text
from cms.models.translated_text import TranslatedText, get_groups_or_offers_cms_reference_object
from cms.models.translated_text_label import TranslatedTextLabel
from webservices.api.serializers.section import SectionSerializer, AchievementSectionSerializer, \
    AdmissionConditionSectionSerializer, ContactsSectionSerializer

WS_SECTIONS_TO_SKIP = [CONTACT_INTRO]


class GeneralInformationSerializer(serializers.Serializer):
    language = serializers.CharField(read_only=True)
    acronym = serializers.CharField(source='title', read_only=True)
    year = serializers.IntegerField(source='academic_year.year', read_only=True)
    education_group_type = serializers.CharField(source='node_type.name', read_only=True)
    education_group_type_text = serializers.CharField(source='node_type.value', read_only=True)
    sections = serializers.SerializerMethodField()
    title = serializers.CharField(source='offer_title_fr', read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        lang = kwargs['context']['language']
        acronym = kwargs['context']['acronym'].upper()
        self.instance.language = lang
        if lang != settings.LANGUAGE_CODE_FR[:2]:
            self.fields['title'] = serializers.CharField(source='offer_title_en', read_only=True)
        if self.instance.code == acronym:
            self.fields['acronym'] = serializers.CharField(source='code', read_only=True)

    def get_sections(self, obj):
        datas = []
        sections = []
        language = settings.LANGUAGE_CODE_FR \
            if self.instance.language == settings.LANGUAGE_CODE_FR[:2] else self.instance.language
        pertinent_sections = general_information_sections.SECTIONS_PER_OFFER_TYPE[obj.node_type.name]
        reference = translated_text.get_groups_or_offers_cms_reference_object(obj).pk

        cms_serializers = {
            SKILLS_AND_ACHIEVEMENTS: AchievementSectionSerializer,
            ADMISSION_CONDITION: AdmissionConditionSectionSerializer,
            CONTACTS: ContactsSectionSerializer,
        }
        extra_intro_offers = self._get_intro_offers(obj)
        for specific_section in pertinent_sections['specific']:
            serializer = cms_serializers.get(specific_section)
            if serializer:
                serializer = serializer({'id': specific_section}, context={
                    'root_node': obj,
                    'language': language,
                    'offer': self.context.get('offer')
                })
                datas.append(serializer.data)
            elif specific_section not in WS_SECTIONS_TO_SKIP:
                sections.append(self._get_section_cms(obj, specific_section, language, reference))

        for offer in extra_intro_offers:
            sections.append(self._get_section_cms(offer, 'intro', language))

        datas += SectionSerializer(sections, many=True).data
        return datas

    def _get_section_cms(self, node, section, language, reference: int = None):
        if reference is None:
            reference = get_groups_or_offers_cms_reference_object(node).pk
        entity = entity_name.get_offers_or_groups_entity_from_node(node)
        translated_text_label = TranslatedTextLabel.objects.get(
            text_label__label=section,
            language=language,
            text_label__entity=entity
        )
        translated_text = TranslatedText.objects.filter(
            text_label__label=section,
            language=language,
            entity=entity,
            reference=reference
        ).annotate(
            label=Value(self._get_correct_label_name(node, section), output_field=CharField()),
            translated_label=Value(translated_text_label.label, output_field=CharField())
        )

        try:
            return translated_text.values('label', 'translated_label', 'text').get()
        except ObjectDoesNotExist:
            return {
                'label': self._get_correct_label_name(node, section),
                'translated_label': translated_text_label.label,
                'text': None,
            }

    @staticmethod
    def _get_correct_label_name(node, section):
        if section == INTRODUCTION:
            return 'intro-' + node.code.lower()
        return section

    @staticmethod
    def _get_intro_offers(obj):
        extra_intro_offers = list(obj.get_finality_list()) + list(obj.get_option_list())
        for e in obj.children:
            if e.child.node_type == GroupType.COMMON_CORE:
                extra_intro_offers.append(e.child)
        return extra_intro_offers
