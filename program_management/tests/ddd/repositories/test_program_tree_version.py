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
from unittest.mock import patch

from django.test import TestCase

from base.models.education_group_year import EducationGroupYear
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.education_group_type import TrainingEducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from education_group.ddd.domain.exception import TrainingNotFoundException
from education_group.models.group_year import GroupYear
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.ddd.domain.node import Node
from program_management.ddd.domain.program_tree_version import NOT_A_TRANSITION
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.models.education_group_version import EducationGroupVersion
from program_management.tests.ddd.factories.program_tree import ProgramTreeFactory
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionFactory, \
    ProgramTreeVersionIdentityFactory
from program_management.tests.factories.education_group_version import EducationGroupVersionFactory
from program_management.tests.factories.element import ElementFactory


class TestVersionRepositoryCreateMethod(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.year = cls.academic_year.year
        cls.type = TrainingEducationGroupTypeFactory()
        cls.repository = ProgramTreeVersionRepository()
        cls.new_program_tree = ProgramTreeFactory(
            root_node__year=cls.year,
            root_node__start_year=cls.year,
            root_node__end_year=cls.year,
            root_node__node_type=TrainingType[cls.type.name],
        )
        cls.new_program_tree_version = ProgramTreeVersionFactory(
            program_tree_identity=cls.new_program_tree.entity_id,
            tree=cls.new_program_tree,
            end_year_of_existence=cls.academic_year.year,
        )
        cls.entity_identity = cls.new_program_tree_version.entity_identity
        cls.database_offer = EducationGroupYearFactory(
            academic_year=cls.academic_year,
            education_group_type=cls.type,
            acronym=cls.entity_identity.offer_acronym,
        )

    @patch.object(Node, '_has_changed', return_value=True)
    def test_simple_case_creation(self, *mocks):
        GroupYearFactory(
            partial_acronym=self.new_program_tree_version.program_tree_identity.code,
            academic_year__year=self.year
        )

        self.repository.create(self.new_program_tree_version)

        education_group_year_db_objects = EducationGroupYear.objects.filter(
            acronym=self.entity_identity.offer_acronym,
            academic_year__year=self.entity_identity.year,
        )

        education_group_version_db_object = EducationGroupVersion.objects.get(
            offer__acronym=self.new_program_tree_version.entity_id.offer_acronym,
            offer__academic_year__year=self.new_program_tree_version.entity_id.year,
            version_name=self.new_program_tree_version.entity_id.version_name,
            transition_name=self.new_program_tree_version.entity_id.transition_name,
        )

        group_year_db_object = GroupYear.objects.get(
            partial_acronym=self.new_program_tree.root_node.code,
            academic_year__year=self.new_program_tree.root_node.year,
        )

        self.assertEqual(len(education_group_year_db_objects), 1)
        self.assertEqual(education_group_version_db_object.offer_id, self.database_offer.id)
        self.assertEqual(education_group_version_db_object.root_group, group_year_db_object)
        self.assertEqual(
            education_group_version_db_object.transition_name, self.new_program_tree_version.transition_name
        )
        self.assertEqual(education_group_version_db_object.version_name, self.new_program_tree_version.version_name)
        self.assertEqual(education_group_version_db_object.title_fr, self.new_program_tree_version.title_fr)
        self.assertEqual(education_group_version_db_object.title_en, self.new_program_tree_version.title_en)
        self.assertEqual(
            education_group_version_db_object.root_group.group.end_year.year,
            self.new_program_tree_version.end_year_of_existence
        )

    def test_assert_raises_training_not_found_exception(self):
        tree_version = ProgramTreeVersionFactory(entity_id__offer_acronym='INEXISTING')
        with self.assertRaises(TrainingNotFoundException):
            self.repository.create(tree_version)


class TestProgramTreeVersionRepositoryGetMethod(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.year = AcademicYearFactory(current=True).year
        cls.repository = ProgramTreeVersionRepository()

    def test_field_mapping_with_specific_version_not_transition(self):
        entity_id = ProgramTreeVersionIdentityFactory(year=self.year, transition_name=NOT_A_TRANSITION)
        root_group = ElementFactory(
            group_year=GroupYearFactory(
                academic_year__year=entity_id.year,
                group__end_year=AcademicYearFactory(current=True),
            )
        ).group_year

        education_group_version_model_obj = EducationGroupVersionFactory(
            offer__acronym=entity_id.offer_acronym,
            offer__academic_year__year=entity_id.year,
            version_name=entity_id.version_name,
            transition_name=entity_id.transition_name,
            root_group=root_group,
        )

        version_tree_domain_obj = self.repository.get(entity_id)

        self.assertEqual(version_tree_domain_obj.entity_id, entity_id)
        self.assertEqual(
            version_tree_domain_obj.entity_id.offer_acronym, education_group_version_model_obj.offer.acronym
        )
        self.assertEqual(
            version_tree_domain_obj.entity_id.year, education_group_version_model_obj.offer.academic_year.year
        )
        self.assertEqual(
            version_tree_domain_obj.entity_id.version_name, education_group_version_model_obj.version_name
        )
        self.assertEqual(
            version_tree_domain_obj.entity_id.transition_name, education_group_version_model_obj.transition_name
        )
        self.assertEqual(
            version_tree_domain_obj.end_year_of_existence, root_group.group.end_year.year
        )
        self.assertEqual(
            version_tree_domain_obj.start_year, root_group.group.start_year.year
        )

    def test_field_mapping_with_transition_version(self):
        entity_id = ProgramTreeVersionIdentityFactory(year=self.year, transition_name='Transition')
        root_group = ElementFactory(
            group_year=GroupYearFactory(
                academic_year__year=entity_id.year,
                group__end_year=AcademicYearFactory(current=True),
            )
        ).group_year

        education_group_version_model_obj = EducationGroupVersionFactory(
            offer__acronym=entity_id.offer_acronym,
            offer__academic_year__year=entity_id.year,
            version_name=entity_id.version_name,
            transition_name=entity_id.transition_name,
            root_group=root_group,
        )

        version_tree_domain_obj = self.repository.get(entity_id)

        self.assertEqual(version_tree_domain_obj.entity_id, entity_id)
        self.assertEqual(
            version_tree_domain_obj.entity_id.offer_acronym, education_group_version_model_obj.offer.acronym
        )
        self.assertEqual(
            version_tree_domain_obj.entity_id.year, education_group_version_model_obj.offer.academic_year.year
        )
        self.assertEqual(
            version_tree_domain_obj.entity_id.version_name, education_group_version_model_obj.version_name
        )
        self.assertEqual(
            version_tree_domain_obj.entity_id.transition_name, education_group_version_model_obj.transition_name
        )
        self.assertEqual(
            version_tree_domain_obj.end_year_of_existence, root_group.group.end_year.year
        )
        self.assertEqual(
            version_tree_domain_obj.start_year, root_group.group.start_year.year
        )
