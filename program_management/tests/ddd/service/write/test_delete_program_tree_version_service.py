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
from unittest import mock
from django.test import TestCase

from base.models.group_element_year import GroupElementYear
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from education_group.models.group_year import GroupYear
from program_management.ddd.command import DeleteProgramTreeVersionCommand
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity
from program_management.ddd.service.write import delete_program_tree_version_service
from program_management.models.education_group_version import EducationGroupVersion
from program_management.models.element import Element
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementGroupYearFactory

GROUP_ELEMENT_YEARS = 'group_element_years'
ELEMENTS = 'elements'
GROUP_YEARS = 'group_years'
EDUCATION_GROUP_VERSION = 'education_group_version'


class TestDeleteVersion(TestCase):

    def setUp(self):
        """
            (education_group_version)
            root_node
            |-link_level_1
              |-link_level_2
                |-- leaf
        """
        self.data = {}
        self.academic_year = AcademicYearFactory()
        self.previous_academic_year = AcademicYearFactory(year=self.academic_year.year - 1)
        self.next_academic_year = AcademicYearFactory(year=self.academic_year.year+1)

        self.data.update(build_version_content(self.academic_year))
        self.data.update(build_version_content(self.next_academic_year))
        self.data.update(build_version_content(self.previous_academic_year))


    def test_delete_version_last_year_only(self):
        education_group_version_to_delete = self.data.get(self.next_academic_year).get(EDUCATION_GROUP_VERSION)

        identity = DeleteProgramTreeVersionCommand(offer_acronym=education_group_version_to_delete.offer.acronym,
                                                   year=education_group_version_to_delete.offer.academic_year.year,
                                                   version_name=education_group_version_to_delete.version_name,
                                                   is_transition=education_group_version_to_delete.is_transition)

        delete_program_tree_version_service.delete_program_tree_version(identity)
        expected_for_ac_yr = self.data.get(self.academic_year)
        expected_for_previous_ac_yr = self.data.get(self.previous_academic_year)

        self.assertEqual_remaining_records(
            expected_for_ac_yr.get(GROUP_ELEMENT_YEARS) + expected_for_previous_ac_yr.get(GROUP_ELEMENT_YEARS),
            expected_for_ac_yr.get(ELEMENTS) + expected_for_previous_ac_yr.get(ELEMENTS),
            expected_for_ac_yr.get(GROUP_YEARS) + expected_for_previous_ac_yr.get(GROUP_YEARS),
            [expected_for_ac_yr.get(EDUCATION_GROUP_VERSION), expected_for_previous_ac_yr.get(EDUCATION_GROUP_VERSION)]
        )

    def test_delete_version_keep_previous_year(self):
        education_group_version_to_delete = self.data.get(self.academic_year).get('education_group_version')
        identity = ProgramTreeVersionIdentity(offer_acronym=education_group_version_to_delete.offer.acronym,
                                              year=education_group_version_to_delete.offer.academic_year.year,
                                              version_name=education_group_version_to_delete.version_name,
                                              is_transition=education_group_version_to_delete.is_transition)
        delete_program_tree_version_service.delete_program_tree_version(identity)
        results_expected_for_previous_academic_year = self.data.get(self.previous_academic_year)

        self.assertEqual_remaining_records(results_expected_for_previous_academic_year.get(GROUP_ELEMENT_YEARS),
                                           results_expected_for_previous_academic_year.get(ELEMENTS),
                                           results_expected_for_previous_academic_year.get(GROUP_YEARS),
                                           [results_expected_for_previous_academic_year.get(EDUCATION_GROUP_VERSION)])

    def test_delete_version_all_years(self):
        education_group_version_to_delete = self.data.get(self.previous_academic_year).get(EDUCATION_GROUP_VERSION)
        identity = ProgramTreeVersionIdentity(offer_acronym=education_group_version_to_delete.offer.acronym,
                                              year=education_group_version_to_delete.offer.academic_year.year,
                                              version_name=education_group_version_to_delete.version_name,
                                              is_transition=education_group_version_to_delete.is_transition)
        delete_program_tree_version_service.delete_program_tree_version(identity)
        self.assertEqual_remaining_records([],
                                           [],
                                           [],
                                           [])

    def assertEqual_remaining_records(self, group_element_years, elements, group_years, education_group_versions):
        results = GroupElementYear.objects.all()
        self.assertListEqual(list(results), group_element_years)
        results = Element.objects.all()
        self.assertListEqual(list(results), elements)
        results = GroupYear.objects.all()
        self.assertListEqual(list(results), group_years)
        results = EducationGroupVersion.objects.all()
        self.assertEqual(list(results), education_group_versions)


def build_version_content(academic_year):
    offer = EducationGroupYearFactory(acronym='LCHIM',
                                      academic_year=academic_year)

    root_node = ElementGroupYearFactory(group_year__group__start_year=academic_year,
                                        group_year__academic_year=academic_year)
    link_level_1 = GroupElementYearFactory(parent_element=root_node,
                                           child_element__group_year__group__start_year=academic_year,
                                           child_element__group_year__academic_year=academic_year)
    link_level_2 = GroupElementYearFactory(parent_element=link_level_1.child_element,
                                           child_element__group_year__group__start_year=academic_year,
                                           child_element__group_year__academic_year=academic_year)
    education_group_version = EducationGroupVersionFactory(
        root_group=root_node.group_year,
        offer=offer,
        version_name='CEMS',
        is_transition=False
    )
    group_years = [
        root_node.group_year,
        link_level_1.child_element.group_year,
        link_level_2.child_element.group_year
    ]
    group_element_years = [link_level_1, link_level_2]

    return {
        academic_year: {
            EDUCATION_GROUP_VERSION: education_group_version,
            GROUP_YEARS: group_years,
            GROUP_ELEMENT_YEARS: group_element_years,
            ELEMENTS: [link_level_1.parent_element, link_level_1.child_element, link_level_2.child_element]
        }
    }
