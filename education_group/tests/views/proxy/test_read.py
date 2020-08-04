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

from django.test import TestCase
from django.urls import reverse

from base.models.enums.education_group_types import MiniTrainingType, TrainingType, GroupType
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import PersonWithPermissionsFactory
from education_group.views.mini_training.common_read import Tab
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory

ACADEMIC_YEAR_YEAR = 2019
START_OF_URL_WHEN_CLICKING_IN_TREE = "/program_management/"


class TestReadTabsRedirection(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.person = PersonWithPermissionsFactory('view_educationgroup')

        cls.training_version = EducationGroupVersionFactory(
            offer__acronym="DROI2M",
            offer__partial_acronym="LDROI200M",
            offer__academic_year__year=ACADEMIC_YEAR_YEAR,
            offer__education_group_type__name=TrainingType.PGRM_MASTER_120.name,
            root_group__acronym="DROI2M",
            root_group__partial_acronym="LDROI200M",
            root_group__academic_year__year=ACADEMIC_YEAR_YEAR,
            root_group__education_group_type__name=TrainingType.PGRM_MASTER_120.name,
        )
        training_root_element = ElementGroupYearFactory(group_year=cls.training_version.root_group)
        cls.url_training = reverse('training_content', kwargs={'year': ACADEMIC_YEAR_YEAR, 'code': 'LDROI200M'})
        #
        cls.mini_training_version = EducationGroupVersionFactory(
            offer__acronym="APPBIOL",
            offer__academic_year__year=ACADEMIC_YEAR_YEAR,
            offer__education_group_type__name=MiniTrainingType.DEEPENING.name,
            root_group__partial_acronym="LBIOL100P",
            root_group__academic_year__year=ACADEMIC_YEAR_YEAR,
            root_group__education_group_type__name=MiniTrainingType.DEEPENING.name,
        )
        child_mini_training_element = ElementGroupYearFactory(group_year=cls.mini_training_version.root_group)
        #
        cls.group_version = EducationGroupVersionFactory(
            offer__acronym="CRIM1PM",
            offer__academic_year__year=ACADEMIC_YEAR_YEAR,
            offer__education_group_type__name=GroupType.FINALITY_120_LIST_CHOICE.name,
            root_group__partial_acronym="LCRIM400K",
            root_group__academic_year__year=ACADEMIC_YEAR_YEAR,
            root_group__education_group_type__name=GroupType.FINALITY_120_LIST_CHOICE.name,
        )
        child_group_element = ElementGroupYearFactory(group_year=cls.group_version.root_group)
        #
        GroupElementYearFactory(parent_element=training_root_element, child_element=child_mini_training_element)
        GroupElementYearFactory(parent_element=training_root_element, child_element=child_group_element)

        cls.url_training_achievements = reverse('mini_training_skills_achievements',
                                                kwargs={'year': ACADEMIC_YEAR_YEAR, 'code': 'LBIOL100P'})
        cls.url_training_general_info = reverse('mini_training_general_information',
                                                kwargs={'year': ACADEMIC_YEAR_YEAR, 'code': 'LBIOL100P'})
        cls.url_mini_training_content = reverse('mini_training_content',
                                                kwargs={'year': ACADEMIC_YEAR_YEAR, 'code': 'LBIOL100P'})

    def setUp(self) -> None:
        self.client.force_login(self.person.user)

    def test_keep_active_tab_content_ok(self):
        header = {'HTTP_REFERER': self.url_mini_training_content}

        response = self.client.get('{}{}/{}/'.format(
            START_OF_URL_WHEN_CLICKING_IN_TREE, ACADEMIC_YEAR_YEAR,
            self.training_version.root_group.partial_acronym
        ), follow=True, **header)
        self.assertTrue(response.context['tab_urls'][Tab.CONTENT]['active'])

    def test_keep_active_tab_achievements_not_available_for_group(self):
        header = {'HTTP_REFERER': self.url_training_achievements}

        response = self.client.get('{}{}/{}/'.format(
            START_OF_URL_WHEN_CLICKING_IN_TREE, ACADEMIC_YEAR_YEAR,
            self.group_version.root_group.partial_acronym
        ), follow=True, **header)
        self.assertTrue(response.context['tab_urls'][Tab.IDENTIFICATION]['active'])

    def test_keep_active_tab_general_information_not_available_for_group_other_than_common_core(self):
        header = {'HTTP_REFERER': self.url_training_general_info}

        response = self.client.get('{}{}/{}/'.format(
            START_OF_URL_WHEN_CLICKING_IN_TREE, ACADEMIC_YEAR_YEAR,
            self.group_version.root_group.partial_acronym
        ), follow=True, **header)
        self.assertTrue(response.context['tab_urls'][Tab.IDENTIFICATION]['active'])
