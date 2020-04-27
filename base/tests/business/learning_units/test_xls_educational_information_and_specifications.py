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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

import datetime

from django.conf import settings
from django.db.models.expressions import Subquery, OuterRef
from django.test import RequestFactory, override_settings
from django.test import TestCase
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from backoffice.settings.base import LANGUAGE_CODE_FR, LANGUAGE_CODE_EN
from base.business.learning_unit import CMS_LABEL_PEDAGOGY_FR_ONLY, \
    CMS_LABEL_PEDAGOGY_FR_AND_EN, CMS_LABEL_SPECIFICATIONS
from base.business.learning_units.xls_educational_information_and_specifications import _get_titles, \
    _add_cms_title_fr_en, prepare_xls_educational_information_and_specifications
from base.models.entity_version import EntityVersion
from base.models.enums import entity_type
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.organization_type import MAIN
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_achievement import LearningAchievementFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.teaching_material import TeachingMaterialFactory
from base.tests.factories.user import UserFactory
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory
from cms.tests.factories.translated_text_label import TranslatedTextLabelFactory
from reference.tests.factories.language import LanguageFactory, FrenchLanguageFactory, EnglishLanguageFactory

INDEX_FIRST_CMS_LABEL_PEDAGOGY_FR_AND_EN_COLUMN = 3
INDEX_FIRST_CMS_LABEL_PEDAGOGY_FR_ONLY_COLUMN = 14
INDEX_FIRST_CMS_LABEL_SPECIFICATIONS_COLUMN = 16

ENTITY_ACRONYM = 'ESPO'
ACRONYM_ALLOCATION = 'INFO'
ACRONYM_REQUIREMENT = 'DRT'

LEARNING_UNIT_YEAR = 'learning_unit_year'
PREFIX_FAKE_LABEL = "cms_"
PREFIX_FAKE_TEXT_LABEL = "text_"


class TestXlsEducationalInformationSpecificationXls(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls._create_luy()
        cls._set_entities()
        cls._create_cms_data()
        cls.teaching_material = TeachingMaterialFactory(learning_unit_year=cls.l_unit_yr_1, 
                                                        title='Teaching material title')
        cls.learning_unit_achievement_fr = LearningAchievementFactory(learning_unit_year=cls.l_unit_yr_1, 
                                                                      language=FrenchLanguageFactory())
        cls.learning_unit_achievement_en = LearningAchievementFactory(learning_unit_year=cls.l_unit_yr_1, 
                                                                      language=EnglishLanguageFactory())
        cls.entity_requirement = EntityVersion.objects.filter(
            entity=OuterRef('learning_container_year__requirement_entity'),
        ).current(
            OuterRef('academic_year__start_date')
        ).values('acronym')[:1]

    @classmethod
    def _create_cms_data(cls):
        cls._create_needed_cms_label(CMS_LABEL_PEDAGOGY_FR_AND_EN + CMS_LABEL_SPECIFICATIONS, True)
        cls._create_needed_cms_label(CMS_LABEL_PEDAGOGY_FR_ONLY, False)

    @classmethod
    def _create_needed_cms_label(cls, cms_labels, with_en):
        for idx, cms_label in enumerate(cms_labels):
            tl = TextLabelFactory(label=cms_label, entity=LEARNING_UNIT_YEAR)
            TranslatedTextLabelFactory(text_label=tl,
                                       language=LANGUAGE_CODE_FR,
                                       label="{}{}".format(PREFIX_FAKE_LABEL, cms_label))
            TranslatedTextLabelFactory(text_label=tl,
                                       language=LANGUAGE_CODE_EN,
                                       label="{}{}".format(PREFIX_FAKE_LABEL, cms_label))
            TranslatedTextFactory(language=LANGUAGE_CODE_FR,
                                  text="{}{} - FR".format(PREFIX_FAKE_TEXT_LABEL, cms_label),
                                  text_label=tl,
                                  reference=cls.l_unit_yr_1.id,
                                  entity=LEARNING_UNIT_YEAR)
            if with_en:
                TranslatedTextFactory(language=LANGUAGE_CODE_EN,
                                      text="{}{} - EN".format(PREFIX_FAKE_TEXT_LABEL, cms_label),
                                      text_label=tl,
                                      reference=cls.l_unit_yr_1.id,
                                      entity=LEARNING_UNIT_YEAR)

    @classmethod
    @override_settings(YEAR_LIMIT_LUE_MODIFICATION=2018)
    def _create_luy(cls):
        academic_year = create_current_academic_year()
        start_year = AcademicYearFactory(year=settings.YEAR_LIMIT_LUE_MODIFICATION-1)
        cls.learning_unit = LearningUnitFactory(start_year=start_year)
        l_container_year = LearningContainerYearFactory(acronym="LBIR1212",
                                                        academic_year=academic_year)
        cls.l_unit_yr_1 = LearningUnitYearFactory(acronym="LBIR1212",
                                                  learning_container_year=l_container_year,
                                                  academic_year=academic_year,
                                                  subtype=learning_unit_year_subtypes.FULL)
        entity_requirement_ver = EntityVersionFactory(acronym=ACRONYM_REQUIREMENT,
                                                      entity=EntityFactory())
        cls.l_unit_yr_1.entity_requirement = entity_requirement_ver.acronym

    @classmethod
    def _set_entities(cls):
        today = datetime.date.today()
        an_entity = EntityFactory(organization=OrganizationFactory(type=MAIN))
        cls.entity_version = EntityVersionFactory(entity=an_entity, entity_type=entity_type.SCHOOL,
                                                  start_date=today.replace(year=1900),
                                                  end_date=None,
                                                  acronym=ENTITY_ACRONYM)
        cls.l_unit_yr_1.learning_container_year.requirement_entity = cls.entity_version.entity
        cls.l_unit_yr_1.learning_container_year.save()

    def test_titles(self):
        titles = _get_titles()
        titles_expected = [
            str(_('Code')),
            str(_('Title')),
            str(_('Req. Entity')),
            str('cms_resume - FR-BE'),
            str('cms_resume - EN'),
            str("cms_teaching_methods - FR-BE"),
            str('cms_teaching_methods - EN'),
            str("cms_evaluation_methods - FR-BE"),
            str('cms_evaluation_methods - EN'),
            str('cms_other_informations - FR-BE'),
            str('cms_other_informations - EN'),
            str('cms_online_resources - FR-BE'),
            str('cms_online_resources - EN'),
            str(_('Teaching material')),
            str("cms_bibliography - FR-BE"),
            str("cms_mobility - FR-BE"),
            str('cms_themes_discussed - FR-BE'),
            str('cms_themes_discussed - EN'),
            str('cms_prerequisite - FR-BE'),
            str('cms_prerequisite - EN'),
            str("{} - {}".format(str(_('Learning achievements')), LANGUAGE_CODE_FR.upper())),
            str("{} - {}".format(str('Learning achievements'), LANGUAGE_CODE_EN.upper()))
        ]

        for idx, title in enumerate(titles):
            self.assertEqual(title, titles_expected[idx])

    def test_prepare_xls_educational_information_and_specifications(self):
        self.a_user = UserFactory(username='dupontm')
        self.person = PersonFactory(user=self.a_user, last_name='dupont', first_name='marcel')
        self.client.force_login(self.person.user)

        request_factory = RequestFactory()
        request = request_factory.post(
            reverse('learning_units'),
            data={'academic_year_id': self.l_unit_yr_1.academic_year.id, 'acronym': self.l_unit_yr_1.acronym}
        )
        request.user = self.a_user

        qs = LearningUnitYear.objects.filter(pk=self.l_unit_yr_1.pk).annotate(
            entity_requirement=Subquery(self.entity_requirement)
        )

        working_sheet_data = prepare_xls_educational_information_and_specifications(
            qs, request)

        self.assertEqual(working_sheet_data[0][0], self.l_unit_yr_1.acronym)
        self.assertEqual(working_sheet_data[0][1], self.l_unit_yr_1.complete_title)
        self.assertEqual(working_sheet_data[0][2], ENTITY_ACRONYM)

        idx = INDEX_FIRST_CMS_LABEL_PEDAGOGY_FR_AND_EN_COLUMN
        for cms_label in CMS_LABEL_PEDAGOGY_FR_AND_EN:
            self.assertEqual(working_sheet_data[0][idx], "{}{} - FR".format(PREFIX_FAKE_TEXT_LABEL, cms_label))
            self.assertEqual(working_sheet_data[0][idx+1], "{}{} - EN".format(PREFIX_FAKE_TEXT_LABEL, cms_label))
            idx += 2

        # teaching material
        self.assertEqual(working_sheet_data[0][13], self.teaching_material.title)
        #
        idx = INDEX_FIRST_CMS_LABEL_PEDAGOGY_FR_ONLY_COLUMN
        for cms_label in CMS_LABEL_PEDAGOGY_FR_ONLY:
            self.assertEqual(working_sheet_data[0][idx], "{}{} - FR".format(PREFIX_FAKE_TEXT_LABEL, cms_label))
            idx += 1
        # specifications
        idx = INDEX_FIRST_CMS_LABEL_SPECIFICATIONS_COLUMN
        for cms_label in CMS_LABEL_SPECIFICATIONS:
            self.assertEqual(working_sheet_data[0][idx], "{}{} - FR".format(PREFIX_FAKE_TEXT_LABEL, cms_label))
            self.assertEqual(working_sheet_data[0][idx+1], "{}{} - EN".format(PREFIX_FAKE_TEXT_LABEL, cms_label))
            idx += 2

        # achievements
        self.assertEqual(working_sheet_data[0][idx], self.learning_unit_achievement_fr.text)
        self.assertEqual(working_sheet_data[0][idx+1], self.learning_unit_achievement_en.text)

    def test_add_cms_title_fr_en(self):
        titles = _add_cms_title_fr_en([CMS_LABEL_PEDAGOGY_FR_AND_EN[0]], False)
        self.assertCountEqual(titles, ["{}{} - {}".format(PREFIX_FAKE_LABEL,
                                                          CMS_LABEL_PEDAGOGY_FR_AND_EN[0],
                                                          LANGUAGE_CODE_FR.upper())])

        titles = _add_cms_title_fr_en([CMS_LABEL_PEDAGOGY_FR_AND_EN[0]], True)
        self.assertCountEqual(
            titles,
            ["{}{} - {}".format(PREFIX_FAKE_LABEL, CMS_LABEL_PEDAGOGY_FR_AND_EN[0], LANGUAGE_CODE_FR.upper()),
             "{}{} - {}".format(PREFIX_FAKE_LABEL, CMS_LABEL_PEDAGOGY_FR_AND_EN[0], LANGUAGE_CODE_EN.upper())]
        )
