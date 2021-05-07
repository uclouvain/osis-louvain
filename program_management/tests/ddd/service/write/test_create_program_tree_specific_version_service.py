# ############################################################################
#  OSIS stands for Open Student Information System. It's an application
#  designed to manage the core business of higher education institutions,
#  such as universities, faculties, institutes and professional schools.
#  The core business involves the administration of students, teachers,
#  courses, programs and so on.
#
#  Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  A copy of this license - GNU General Public License - is available
#  at the root of the source code of this program.  If not,
#  see http://www.gnu.org/licenses/.
# ############################################################################
from unittest.mock import patch

from django.test import TestCase

from base.models.enums.education_group_types import GroupType, TrainingType
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.authorized_relationship import AuthorizedRelationshipFactory
from base.tests.factories.campus import CampusFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.validation_rule import ValidationRuleFactory
from education_group.tests.ddd.factories.command.create_and_postpone_training_and_tree_command import \
    CreateAndPostponeTrainingAndProgramTreeCommandFactory
from program_management.ddd.command import CreateProgramTreeSpecificVersionCommand
from program_management.ddd.domain.exception import ProgramTreeVersionNotFoundException
from program_management.ddd.domain.program_tree_version import ProgramTreeVersionIdentity, STANDARD, NOT_A_TRANSITION
from program_management.ddd.repositories.program_tree_version import ProgramTreeVersionRepository
from program_management.ddd.service.write import create_program_tree_specific_version_service
from program_management.ddd.service.write.create_training_with_program_tree import \
    create_and_report_training_with_program_tree
from program_management.tests.ddd.factories.program_tree_version import ProgramTreeVersionFactory
from reference.tests.factories.language import LanguageFactory


class TestCreateProgramTreeVersion(TestCase):
    def setUp(self) -> None:
        self.offer_acronym = 'DROI2M'
        self.current_year = 2018
        self.end_year_standard_version = 2023
        self.standard_version = ProgramTreeVersionFactory.produce_standard_2M_program_tree(
            current_year=self.current_year,
            end_year=self.end_year_standard_version
        )
        self.command = CreateProgramTreeSpecificVersionCommand(
            end_year=self.end_year_standard_version,
            offer_acronym=self.offer_acronym,
            version_name='CEMS',
            start_year=self.standard_version.entity_identity.year,
            transition_name=NOT_A_TRANSITION,
            title_en='Title in English',
            title_fr='Intitulé en français',
        )

    def _create_standard_version(self):
        cmd = CreateAndPostponeTrainingAndProgramTreeCommandFactory(
            abbreviated_title=self.offer_acronym,
            year=self.current_year,
            start_year=self.current_year,
            code='LDROI200M',
            type=TrainingType.PGRM_MASTER_120.name,
            # TODO: Fix main_language FK....
            main_language=LanguageFactory()
        )

        # TODO :: mock all DB access with fake repository
        EntityVersionFactory(acronym=cmd.management_entity_acronym)
        CampusFactory(name=cmd.teaching_campus_name, organization__name=cmd.teaching_campus_organization_name)
        AcademicYearFactory.produce_in_future(cmd.year)
        root_type = EducationGroupTypeFactory(name=cmd.type)
        ValidationRuleFactory(
            field_reference="TrainingForm.PGRM_MASTER_120.title_fr",
            initial_value="Master [120] en",
        )
        ValidationRuleFactory(
            field_reference="TrainingForm.PGRM_MASTER_120.code",
            initial_value="200M",
        )
        self.credit_rule = ValidationRuleFactory(
            field_reference="TrainingVersionForm.PGRM_MASTER_120.credits",
            initial_value=100,
        )
        AuthorizedRelationshipFactory(
            parent_type=root_type,
            child_type=EducationGroupTypeFactory(name=GroupType.COMMON_CORE.name),
            min_count_authorized=1,
        )
        ValidationRuleFactory(
            field_reference="GroupForm.COMMON_CORE.abbreviated_title",
            initial_value="PARTIEDEBASE",
        )
        ValidationRuleFactory(
            field_reference="GroupForm.COMMON_CORE.title_fr",
            initial_value="	Contenu: ",
        )
        ValidationRuleFactory(
            field_reference="GroupForm.COMMON_CORE.code",
            initial_value="100T",
        )
        AuthorizedRelationshipFactory(
            parent_type=root_type,
            child_type=EducationGroupTypeFactory(name=GroupType.FINALITY_120_LIST_CHOICE.name),
            min_count_authorized=1,
        )
        ValidationRuleFactory(
            field_reference="GroupForm.FINALITY_120_LIST_CHOICE.abbreviated_title",
            initial_value="",
        )
        ValidationRuleFactory(
            field_reference="GroupForm.FINALITY_120_LIST_CHOICE.title_fr",
            initial_value="List au choix",
        )
        ValidationRuleFactory(
            field_reference="GroupForm.FINALITY_120_LIST_CHOICE.code",
            initial_value="400G",
        )
        AuthorizedRelationshipFactory(
            parent_type=root_type,
            child_type=EducationGroupTypeFactory(name=GroupType.OPTION_LIST_CHOICE.name),
            min_count_authorized=1,
        )
        ValidationRuleFactory(
            field_reference="GroupForm.OPTION_LIST_CHOICE.abbreviated_title",
            initial_value="",
        )
        ValidationRuleFactory(
            field_reference="GroupForm.OPTION_LIST_CHOICE.title_fr",
            initial_value="List au choix options",
        )
        ValidationRuleFactory(
            field_reference="GroupForm.OPTION_LIST_CHOICE.code",
            initial_value="300G",
        )

        training_identities = create_and_report_training_with_program_tree(cmd)
        standard_version_identity = ProgramTreeVersionIdentity(
            offer_acronym=cmd.abbreviated_title,
            year=cmd.year,
            version_name=STANDARD,
            transition_name=NOT_A_TRANSITION,
        )

        return training_identities, standard_version_identity

    def test_when_tree_version_standard_does_not_exist(self):
        with self.assertRaises(ProgramTreeVersionNotFoundException):
            create_program_tree_specific_version_service.create_program_tree_specific_version(self.command)

    @patch("base.business.academic_calendar.AcademicEventCalendarHelper.get_target_years_opened")
    def test_assert_tree_version_correctly_created(self, mock_calendar):
        mock_calendar.return_value = [self.current_year]
        self._create_standard_version()

        identity = create_program_tree_specific_version_service.create_program_tree_specific_version(self.command)

        tree_version_created = ProgramTreeVersionRepository().get(identity)
        tree = tree_version_created.get_tree()

        self.assertEqual(tree_version_created.entity_id.offer_acronym, self.command.offer_acronym)
        self.assertEqual(tree_version_created.entity_id.year, self.command.start_year)
        self.assertEqual(tree_version_created.entity_id.version_name, self.command.version_name)
        self.assertEqual(tree_version_created.entity_id.transition_name, self.command.transition_name)
        self.assertEqual(tree_version_created.title_fr, self.command.title_fr)
        self.assertEqual(tree_version_created.title_en, self.command.title_en)
        self.assertEqual(tree_version_created.end_year_of_existence, self.command.end_year)
        self.assertEqual(tree_version_created.start_year, self.command.start_year)
        self.assertEqual(tree.root_node.credits, self.credit_rule.initial_value)
