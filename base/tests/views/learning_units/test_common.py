############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
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
############################################################################
from django.test import TestCase

from base.models.enums.education_group_categories import Categories
from base.models.enums.education_group_types import TrainingType, GroupType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import TrainingFactory
from base.tests.factories.group_element_year import GroupElementYearChildLeafFactory
from base.views.common import _find_root_trainings_using_element
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.ddd.domain.program_tree_version import STANDARD
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory
from program_management.tests.factories.element import ElementLearningUnitYearFactory

LUY_ACRONYM = 'LECRI1508'


class TestLearningUnitCommonView(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.element_learning_unit_year = ElementLearningUnitYearFactory(
            learning_unit_year__acronym=LUY_ACRONYM,
            learning_unit_year__academic_year=cls.academic_year,
            learning_unit_year__learning_container_year__academic_year=cls.academic_year,
        )

    def test_ue_used_in_one_training(self):
        self.build_training_tree('DROI2M', 'Bachelier droit', self.element_learning_unit_year,
                                 TrainingType.BACHELOR, Categories.TRAINING)
        res = _find_root_trainings_using_element(self.element_learning_unit_year.learning_unit_year.acronym,
                                                 self.academic_year.year)
        expected = ['DROI2M - Bachelier droit']
        self.assertListEqual(res, expected)

    def test_ue_used_in_two_trainings(self):
        self.build_training_tree('DROI2M', 'Bachelier droit', self.element_learning_unit_year,
                                 TrainingType.BACHELOR, Categories.TRAINING)
        self.build_training_tree('ARK1BA', 'Bachelier archi', self.element_learning_unit_year,
                                 TrainingType.BACHELOR, Categories.TRAINING)
        res = _find_root_trainings_using_element(self.element_learning_unit_year.learning_unit_year.acronym,
                                                 self.academic_year.year)
        expected = ['ARK1BA - Bachelier archi',
                    'DROI2M - Bachelier droit']
        self.assertListEqual(res, expected)

    def build_training_tree(self, acronym, title, element_learning_unit_year, education_group_type, category):
        # """
        #    |root_group
        #    |----common_group
        #         |----(element_learning_unit_year)
        # """
        offer = TrainingFactory(academic_year=self.academic_year,
                                title=title)
        root_group = GroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__category=category.name,
            education_group_type__name=education_group_type.name,
            acronym=acronym
        )
        root_element = ElementGroupYearFactory(group_year=root_group)

        common_group = GroupYearFactory(
            academic_year=self.academic_year,
            education_group_type__category=Categories.GROUP.name,
            education_group_type__name=GroupType.COMMON_CORE.name,
            acronym='COMMON'
        )
        common_group_element = ElementGroupYearFactory(group_year=common_group)
        GroupElementYearChildLeafFactory(parent_element=root_element,
                                         child_element=common_group_element)
        if element_learning_unit_year:
            GroupElementYearChildLeafFactory(parent_element=common_group_element,
                                             child_element=element_learning_unit_year)
        EducationGroupVersionFactory(
            offer=offer,
            root_group=root_group,
            version_name=STANDARD,
            title_fr=None
        )
        return root_element
