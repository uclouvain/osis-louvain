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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import datetime

from django.test import TestCase

from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.business import learning_unit_proposal as lu_proposal_business
from base import models as mdl_base

from django.test import TestCase

from base.models.enums import organization_type, proposal_type, entity_type, \
    learning_container_year_types, entity_container_year_link_type, \
    learning_unit_year_subtypes
from base.tests.factories.academic_year import create_current_academic_year
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory
from base.tests.factories.organization import OrganizationFactory


class TestLearningUnitProposal(TestCase):

    def test_get_data_dict(self):
        self.assertIsNone(lu_proposal_business._get_data_dict('key1', None))
        self.assertIsNone(lu_proposal_business._get_data_dict('key1', {'key2': 'nothing serious'}))
        self.assertEqual(lu_proposal_business._get_data_dict('key1', {'key1': 'nothing serious'}), 'nothing serious')


class TestLearningUnitProposalChecks(TestCase):

    def setUp(self):
        today = datetime.date.today()
        self.current_academic_year = AcademicYearFactory(start_date=today,
                                                         end_date=today.replace(year=today.year + 1),
                                                         year=today.year)

        self.learning_unit_year_1 = LearningUnitYearFactory(academic_year=self.current_academic_year)
        self.learning_unit_year_2 = LearningUnitYearFactory(academic_year=self.current_academic_year)
        self.learning_unit_year_3 = LearningUnitYearFactory(academic_year=self.current_academic_year)

        self.proposal_suppression = ProposalLearningUnitFactory(learning_unit_year=self.learning_unit_year_1,
                                                                type=proposal_type.ProposalType.SUPPRESSION.name)
        self.proposal_creation = ProposalLearningUnitFactory(learning_unit_year=self.learning_unit_year_2,
                                                             type=proposal_type.ProposalType.CREATION.name)
        self.proposal_modification = ProposalLearningUnitFactory(learning_unit_year=self.learning_unit_year_3,
                                                                 type=proposal_type.ProposalType.MODIFICATION.name)

    def test_check_proposals_valid_to_get_back_to_initial(self):
        self.assertTrue(lu_proposal_business.check_proposals_valid_to_get_back_to_initial([self.proposal_suppression]))

    def test_check_proposals_invalid_to_get_back_to_initial(self):
        self.assertFalse(lu_proposal_business.check_proposals_valid_to_get_back_to_initial([self.proposal_suppression,
                                                                                            self.proposal_creation]))
        self.assertFalse(lu_proposal_business.check_proposals_valid_to_get_back_to_initial([self.proposal_modification,
                                                                                            self.proposal_creation]))

    def test_get_valid_proposal_for_cancellation(self):
        self.assertEqual(len(lu_proposal_business.get_valid_proposal_for_cancellation([self.proposal_suppression])), 1)
        self.assertCountEqual(lu_proposal_business.get_valid_proposal_for_cancellation([self.proposal_suppression]),
                              [self.proposal_suppression])
        self.assertEqual(len(lu_proposal_business.get_valid_proposal_for_cancellation([self.proposal_creation])), 0)


class TestLearningUnitProposalCancel(TestCase):
    def setUp(self):
        current_academic_year = create_current_academic_year()
        an_organization = OrganizationFactory(type=organization_type.MAIN)
        learning_container_year = LearningContainerYearFactory(
            academic_year=current_academic_year,
            container_type=learning_container_year_types.COURSE,
            campus=CampusFactory(organization=an_organization, is_administration=True)
        )
        self.learning_unit_year = LearningUnitYearFakerFactory(credits=5,
                                                               subtype=learning_unit_year_subtypes.FULL,
                                                               academic_year=current_academic_year,
                                                               learning_container_year=learning_container_year)

        self.entity_container_year = EntityContainerYearFactory(
            learning_container_year=self.learning_unit_year.learning_container_year,
            type=entity_container_year_link_type.REQUIREMENT_ENTITY
        )

        today = datetime.date.today()

        an_entity = EntityFactory(organization=an_organization)
        self.entity_version = EntityVersionFactory(entity=an_entity, entity_type=entity_type.SCHOOL, start_date=today,
                                                   end_date=today.replace(year=today.year + 1))

    def test_cancel_proposal(self):
        self._create_proposal()
        lu_proposal_business.cancel_proposal(self.learning_unit_year)
        self.assertCountEqual(list(mdl_base.proposal_learning_unit.ProposalLearningUnit.objects
                                   .filter(learning_unit_year=self.learning_unit_year)), [])

    def test_cancel_proposals(self):
        proposal = self._create_proposal()
        lu_proposal_business.cancel_proposals([proposal])
        self.assertCountEqual(list(mdl_base.proposal_learning_unit.ProposalLearningUnit.objects
                                   .filter(learning_unit_year=self.learning_unit_year)), [])

    def _create_proposal(self):
        initial_data_expected = {
            "learning_container_year": {
                "id": self.learning_unit_year.learning_container_year.id,
                "acronym": self.learning_unit_year.acronym,
                "common_title": self.learning_unit_year.learning_container_year.common_title,
                "common_title_english": self.learning_unit_year.learning_container_year.common_title_english,
                "container_type": self.learning_unit_year.learning_container_year.container_type,
                "campus": self.learning_unit_year.learning_container_year.campus.id,
                "language": self.learning_unit_year.learning_container_year.language.id,
                "in_charge": self.learning_unit_year.learning_container_year.in_charge
            },
            "learning_unit_year": {
                "id": self.learning_unit_year.id,
                "acronym": self.learning_unit_year.acronym,
                "specific_title": self.learning_unit_year.specific_title,
                "specific_title_english": self.learning_unit_year.specific_title_english,
                "internship_subtype": self.learning_unit_year.internship_subtype,
                "credits": self.learning_unit_year.credits,
                "quadrimester": self.learning_unit_year.quadrimester,
                "status": self.learning_unit_year.status
            },
            "learning_unit": {
                "id": self.learning_unit_year.learning_unit.id,
                "periodicity": self.learning_unit_year.learning_unit.periodicity
            },
            "entities": {
                entity_container_year_link_type.REQUIREMENT_ENTITY: self.entity_container_year.entity.id,
                entity_container_year_link_type.ALLOCATION_ENTITY: None,
                entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1: None,
                entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2: None
            }
        }
        return ProposalLearningUnitFactory(learning_unit_year=self.learning_unit_year,
                                           initial_data=initial_data_expected)
