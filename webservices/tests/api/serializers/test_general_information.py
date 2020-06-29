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
import collections
from unittest import mock

from django.conf import settings
from django.test import TestCase

from base.business.education_groups.general_information_sections import DETAILED_PROGRAM, \
    COMMON_DIDACTIC_PURPOSES, SKILLS_AND_ACHIEVEMENTS, WELCOME_INTRODUCTION, INTRODUCTION
from base.models.enums.education_group_types import GroupType, MiniTrainingType, TrainingType
from base.tests.factories.education_group_year import EducationGroupYearCommonFactory, \
    TrainingFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from cms.enums.entity_name import OFFER_YEAR, GROUP_YEAR
from cms.tests.factories.translated_text import TranslatedTextFactory
from cms.tests.factories.translated_text_label import TranslatedTextLabelFactory
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.ddd.repositories import load_tree
from program_management.tests.ddd.factories.node import NodeGroupYearFactory
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory
from program_management.tests.factories.element import ElementFactory
from webservices.api.serializers.general_information import GeneralInformationSerializer
from webservices.business import EVALUATION_KEY, SKILLS_AND_ACHIEVEMENTS_INTRO, SKILLS_AND_ACHIEVEMENTS_EXTRA


class GeneralInformationSerializerTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.egy = TrainingFactory(education_group_type__name=TrainingType.PGRM_MASTER_120.name)
        cls.group = GroupYearFactory(
            academic_year=cls.egy.academic_year,
            partial_acronym=cls.egy.partial_acronym,
            education_group_type__name=cls.egy.education_group_type.name
        )
        StandardEducationGroupVersionFactory(offer=cls.egy, root_group=cls.group)
        element = ElementFactory(group_year=cls.group)

        cls.common_egy = EducationGroupYearCommonFactory(academic_year=cls.egy.academic_year)
        cls.language = settings.LANGUAGE_CODE_EN
        cls.pertinent_sections = {
            'specific': [DETAILED_PROGRAM, SKILLS_AND_ACHIEVEMENTS],
            'common': [COMMON_DIDACTIC_PURPOSES]
        }
        for section in cls.pertinent_sections['common']:
            TranslatedTextLabelFactory(
                language=cls.language,
                text_label__label=section
            )
            TranslatedTextFactory(
                reference=cls.common_egy.id,
                entity=OFFER_YEAR,
                language=cls.language,
                text_label__label=section,
            )
        for section in cls.pertinent_sections['specific']:
            TranslatedTextLabelFactory(
                language=cls.language,
                text_label__label=section
            )
            TranslatedTextFactory(
                reference=cls.egy.id,
                entity=OFFER_YEAR,
                language=cls.language,
                text_label__label=section
            )
        for label in [SKILLS_AND_ACHIEVEMENTS_INTRO, SKILLS_AND_ACHIEVEMENTS_EXTRA]:
            TranslatedTextFactory(
                text_label__label=label,
                reference=cls.egy.id,
                entity=OFFER_YEAR,
                language=cls.language
            )
        cls.tree = load_tree.load(element.id)
        cls.serializer = GeneralInformationSerializer(
            cls.tree.root_node, context={
                'language': cls.language,
                'acronym': cls.egy.acronym,
                'offer': cls.egy
            }
        )

    def setUp(self):
        patcher_sections = mock.patch(
            'base.business.education_groups.general_information_sections.SECTIONS_PER_OFFER_TYPE',
            _get_mocked_sections_per_offer_type(self.egy, **self.pertinent_sections)
        )
        patcher_sections.start()
        self.addCleanup(patcher_sections.stop)

    def test_contains_expected_fields(self):
        expected_fields = [
            'language',
            'acronym',
            'year',
            'education_group_type',
            'education_group_type_text',
            'sections',
            'title'
        ]
        self.assertListEqual(list(self.serializer.data.keys()), expected_fields)

    def test_ensure_content_field_is_list_of_dict(self):
        expected_fields = [
            'id',
            'label',
            'content',
        ]
        self.assertEqual(type(self.serializer.data['sections']), list)
        self.assertEqual(
            len(self.serializer.data['sections']),
            len(self.pertinent_sections['specific'])
        )
        for section in self.serializer.data['sections']:
            if section['id'] == EVALUATION_KEY:
                self.assertTrue(isinstance(section, dict))
                self.assertListEqual(list(section.keys()), expected_fields + ['free_text'])
            else:
                self.assertTrue(isinstance(section, collections.OrderedDict))
                self.assertListEqual(list(section.keys()), expected_fields)

    def test_case_text_not_existing(self):
        with mock.patch(
                'base.business.education_groups.general_information_sections.SECTIONS_PER_OFFER_TYPE',
                _get_mocked_sections_per_offer_type(self.egy, specific=[WELCOME_INTRODUCTION])
        ):
            TranslatedTextLabelFactory(
                language=self.language,
                text_label__label=WELCOME_INTRODUCTION
            )
            node = NodeGroupYearFactory(
                node_id=self.group.element.id,
                node_type=self.egy.education_group_type,
            )
            welcome_introduction_section = GeneralInformationSerializer(
                node, context={
                    'language': self.language,
                    'acronym': self.egy.acronym
                }
            ).data['sections'][0]
            self.assertIsNone(welcome_introduction_section['content'])


def _get_mocked_sections_per_offer_type(egy, specific=None, common=None):
    return {
        egy.education_group_type.name: {
            'specific': specific or [],
            'common': common or []
        }
    }


class IntroOffersSectionTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.egy = TrainingFactory(education_group_type__name=TrainingType.PGRM_MASTER_120.name)
        cls.group = GroupYearFactory(
            academic_year=cls.egy.academic_year,
            partial_acronym=cls.egy.partial_acronym,
            education_group_type__name=cls.egy.education_group_type.name
        )
        StandardEducationGroupVersionFactory(offer=cls.egy, root_group=cls.group)
        cls.element = ElementFactory(group_year=cls.group)
        EducationGroupYearCommonFactory(academic_year=cls.egy.academic_year)
        cls.language = settings.LANGUAGE_CODE_EN

    def setUp(self):
        patcher_sections = mock.patch(
            'base.business.education_groups.general_information_sections.SECTIONS_PER_OFFER_TYPE',
            _get_mocked_sections_per_offer_type(self.egy)
        )
        patcher_sections.start()
        self.addCleanup(patcher_sections.stop)

    def test_get_intro_offers(self):
        gey = GroupElementYearFactory(
            parent_element=self.element,
            child_element__group_year__education_group_type__name=GroupType.COMMON_CORE.name,
            child_element__group_year__partial_acronym="TESTTC"
        )
        intro_offer_section = self._get_pertinent_intro_section(gey)
        self.assertIsNone(intro_offer_section['content'])
        self.assertEqual(intro_offer_section['id'], 'intro-testtc')

    def test_get_intro_option_offer(self):
        gey = GroupElementYearFactory(
            parent_element=self.element,
            child_element__group_year__education_group_type__name=GroupType.OPTION_LIST_CHOICE.name
        )
        gey_option = GroupElementYearFactory(
            parent_element=gey.child_element,
            child_element__group_year__education_group_type__name=MiniTrainingType.OPTION.name,
            child_element__group_year__partial_acronym="TESTOPTION"
        )
        StandardEducationGroupVersionFactory(root_group=gey_option.child_element.group_year)
        intro_offer_section = self._get_pertinent_intro_section(gey_option)
        self.assertIsNone(intro_offer_section['content'])
        self.assertEqual(intro_offer_section['id'], 'intro-testoption')

    def test_get_intro_finality_offer(self):
        g = GroupElementYearFactory(
            parent_element=self.element,
            child_element__group_year__education_group_type__name=GroupType.FINALITY_120_LIST_CHOICE.name
        )
        gey = GroupElementYearFactory(
            parent_element=g.child_element,
            child_element__group_year__education_group_type__name=TrainingType.MASTER_MD_120.name,
            child_element__group_year__partial_acronym="TESTFINA",
        )
        StandardEducationGroupVersionFactory(root_group=gey.child_element.group_year)
        intro_offer_section = self._get_pertinent_intro_section(gey)
        self.assertIsNone(intro_offer_section['content'])
        self.assertEqual(intro_offer_section['id'], 'intro-testfina')

    def _get_pertinent_intro_section(self, gey):
        entity = GROUP_YEAR if gey.child_element.group_year.education_group_type.name in GroupType.get_names() \
            else OFFER_YEAR
        TranslatedTextLabelFactory(
            text_label__label=INTRODUCTION,
            language=self.language,
            text_label__entity=entity
        )
        TranslatedTextFactory(
            text_label__label=INTRODUCTION,
            language=self.language,
            entity=entity,
            reference=gey.child_branch.id,
            text_label__entity=entity
        )
        tree = load_tree.load(self.element.id)
        node = tree.root_node
        return GeneralInformationSerializer(
            node, context={
                'language': self.language,
                'acronym': node.title
            }
        ).data['sections'][0]
