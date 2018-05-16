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

from factory import fuzzy
from unittest import mock
from unittest.mock import patch

from django.contrib.messages import INFO
from django.contrib.messages import SUCCESS, ERROR
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

from base import models as mdl_base
from base.business import learning_unit_proposal as lu_proposal_business
from base.business.learning_unit_proposal import compute_proposal_type, consolidate_proposal, modify_proposal_state
from base.business.learning_unit_proposal import consolidate_proposals_and_send_report
from base.business.learning_units.perms import PROPOSAL_CONSOLIDATION_ELIGIBLE_STATES
from base.models.academic_year import AcademicYear, LEARNING_UNIT_CREATION_SPAN_YEARS
from base.models.enums import organization_type, proposal_type, entity_type, \
    learning_container_year_types, entity_container_year_link_type, \
    learning_unit_year_subtypes, proposal_state
from base.models.enums.proposal_type import ProposalType
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateContainer
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory, LearningUnitYearFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory


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

    def test_cancel_proposal_of_type_suppression_case_success(self):
        proposal = self._create_proposal(prop_type=proposal_type.ProposalType.SUPPRESSION.name,
                                         prop_state=proposal_state.ProposalState.FACULTY.name)
        lu_proposal_business.cancel_proposal(proposal)
        self.assertCountEqual(list(mdl_base.proposal_learning_unit.ProposalLearningUnit.objects
                                   .filter(learning_unit_year=self.learning_unit_year)), [])

    def test_cancel_proposal_of_type_creation_case_success(self):
        proposal = self._create_proposal(prop_type=proposal_type.ProposalType.CREATION.name,
                                         prop_state=proposal_state.ProposalState.FACULTY.name)
        lu = proposal.learning_unit_year.learning_unit
        lu_proposal_business.cancel_proposal(proposal)
        self.assertCountEqual(list(mdl_base.proposal_learning_unit.ProposalLearningUnit.objects
                                   .filter(learning_unit_year=self.learning_unit_year)), [])
        self.assertCountEqual(list(mdl_base.learning_unit.LearningUnit.objects.filter(id=lu.id)),
                              [])

    @patch("base.business.learning_units.perms.is_eligible_for_cancel_of_proposal",
           side_effect=lambda proposal, person: True)
    @patch('base.utils.send_mail.send_mail_cancellation_learning_unit_proposals')
    def test_cancel_proposals_of_type_suppression(self, mock_send_mail, mock_perm):
        proposal = self._create_proposal(prop_type=proposal_type.ProposalType.SUPPRESSION.name,
                                         prop_state=proposal_state.ProposalState.FACULTY.name)
        proposal.entity = self.entity_container_year.entity
        proposal.save()
        person_entity = PersonEntityFactory(entity=self.entity_container_year.entity)
        lu_proposal_business.cancel_proposals_and_send_report([proposal], person_entity.person, [])
        self.assertCountEqual(list(mdl_base.proposal_learning_unit.ProposalLearningUnit.objects
                                   .filter(learning_unit_year=self.learning_unit_year)), [])
        self.assertTrue(mock_send_mail.called)
        self.assertTrue(mock_perm.called)

    def _create_proposal(self, prop_type, prop_state):
        initial_data_expected = {
            "learning_container_year": {
                "id": self.learning_unit_year.learning_container_year.id,
                "acronym": self.learning_unit_year.acronym,
                "common_title": self.learning_unit_year.learning_container_year.common_title,
                "common_title_english": self.learning_unit_year.learning_container_year.common_title_english,
                "container_type": self.learning_unit_year.learning_container_year.container_type,
                "campus": self.learning_unit_year.learning_container_year.campus.id,
                "language": self.learning_unit_year.learning_container_year.language.pk,
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
                                           initial_data=initial_data_expected,
                                           type=prop_type,
                                           state=prop_state)


class TestComputeProposalType(TestCase):
    def test_return_creation_type_when_creation_is_initial_proposal_type(self):
        proposal = ProposalLearningUnitFactory(type=ProposalType.CREATION.name)
        actual_proposal_type = compute_proposal_type(proposal, proposal.learning_unit_year)
        self.assertEqual(proposal_type.ProposalType.CREATION.name, actual_proposal_type)

    def test_return_suppression_type_when_suppresion_is_initial_proposal_type(self):
        proposal = ProposalLearningUnitFactory(type=ProposalType.SUPPRESSION.name )
        actual_proposal_type = compute_proposal_type(proposal, proposal.learning_unit_year)
        self.assertEqual(proposal_type.ProposalType.SUPPRESSION.name, actual_proposal_type)

    def test_return_transformation_when_data_changed_consist_of_first_letter(self):
        proposal = ProposalLearningUnitFactory(type=ProposalType.MODIFICATION.name, initial_data={
            'learning_unit_year':{'acronym': 'bibi'}})

        actual_proposal_type = compute_proposal_type(proposal, proposal.learning_unit_year)
        self.assertEqual(proposal_type.ProposalType.TRANSFORMATION.name, actual_proposal_type)

    def test_return_modification_when_data_changed_consist_of_other_fields_than_first_letter_or_acronym(self):
        proposal = ProposalLearningUnitFactory(type=ProposalType.MODIFICATION.name, initial_data={
            'learning_container_year':{'common_title': 'bibi'}})
        actual_proposal_type = compute_proposal_type(proposal, proposal.learning_unit_year)
        self.assertEqual(proposal_type.ProposalType.MODIFICATION.name, actual_proposal_type)

    def test_return_modification_when_no_data_changed(self):
        proposal = ProposalLearningUnitFactory(type=ProposalType.MODIFICATION.name, initial_data={})
        actual_proposal_type = compute_proposal_type(proposal, proposal.learning_unit_year)
        self.assertEqual(proposal_type.ProposalType.MODIFICATION.name, actual_proposal_type)

    def test_return_transformation_and_modification_when_modifying_acronym_and_other_field(self):
        proposal = ProposalLearningUnitFactory(type=ProposalType.MODIFICATION.name, initial_data={
            'learning_unit_year': {'acronym': 'bobo'}, 'learning_container_year': {'common_title': 'bibi'}})
        actual_proposal_type = compute_proposal_type(proposal, proposal.learning_unit_year)
        self.assertEqual(proposal_type.ProposalType.TRANSFORMATION_AND_MODIFICATION.name, actual_proposal_type)


def create_academic_years():
    academic_years_to_create = LEARNING_UNIT_CREATION_SPAN_YEARS + 2
    current_academic_year = create_current_academic_year()
    academic_years = [current_academic_year]

    for i in range(1, academic_years_to_create + 1):
        new_academic_year = AcademicYearFactory.build(
            year=current_academic_year.year+i,
            start_date=current_academic_year.start_date + datetime.timedelta(days=365*i),
            end_date=current_academic_year.end_date + datetime.timedelta(days=365 * i))
        super(AcademicYear, new_academic_year).save()
        academic_years.append(new_academic_year)
    return academic_years


class TestConsolidateProposals(TestCase):
    def setUp(self):
        self.author = PersonFactory()
        self.proposals = [ProposalLearningUnitFactory() for _ in range(2)]
        person_entity = PersonEntityFactory(person=self.author)
        for proposal in self.proposals:
            EntityContainerYearFactory(learning_container_year=proposal.learning_unit_year.learning_container_year,
                                       entity=person_entity.entity,
                                       type=entity_container_year_link_type.REQUIREMENT_ENTITY)

    @mock.patch("base.business.learning_units.perms.is_eligible_to_consolidate_proposal",
                side_effect=lambda proposal, person: True)
    @mock.patch("base.business.learning_unit_proposal.consolidate_proposal",
                side_effect=lambda prop: {SUCCESS: ["msg_success"]})
    @mock.patch("base.utils.send_mail.send_mail_consolidation_learning_unit_proposal",
                side_effect=None)
    def test_call_method_consolidate_proposal(self, mock_mail, mock_consolidate_proposal, mock_perm):
        result = consolidate_proposals_and_send_report(self.proposals, self.author, [])

        consolidate_args_list = [((self.proposals[0],),), ((self.proposals[1],),)]
        self.assertListEqual(mock_consolidate_proposal.call_args_list, consolidate_args_list)

        self.assertDictEqual(result, {
            INFO: [_("A report has been sent.")],
            ERROR: [],
            SUCCESS: [_("Proposal %(acronym)s (%(academic_year)s) successfully consolidated.") % {
                "acronym": proposal.learning_unit_year.acronym,
                "academic_year":proposal.learning_unit_year.academic_year
            } for proposal in self.proposals]
        })

        self.assertTrue(mock_mail.called)
        self.assertTrue(mock_perm.called)


def mock_message_by_level(*args, **kwargs):
    return {SUCCESS: ["this is a mock"]}


class TestConsolidateProposal(TestCase):
    def test_when_proposal_is_not_accepted_nor_refused(self):
        states = (state for state, value in proposal_state.ProposalState.__members__.items()
                  if state not in PROPOSAL_CONSOLIDATION_ELIGIBLE_STATES )
        for state in states:
            with self.subTest(state=state):
                proposal = ProposalLearningUnitFactory(state=state)
                result = consolidate_proposal(proposal)
                expected_result = {
                    ERROR: [_("Proposal is neither accepted nor refused.")]
                }
                self.assertDictEqual(result, expected_result)

    @mock.patch("base.business.learning_unit_proposal.cancel_proposal", side_effect=mock_message_by_level)
    def test_when_proposal_is_refused(self, mock_cancel_proposal):
        proposal_refused = ProposalLearningUnitFactory(state=proposal_state.ProposalState.REFUSED.name)

        consolidate_proposal(proposal_refused)

        mock_cancel_proposal.assert_called_once_with(proposal_refused)

    @mock.patch("base.business.learning_unit_proposal.edit_learning_unit_end_date")
    def test_when_proposal_of_type_creation_and_accepted(self, mock_edit_lu_end_date):
        creation_proposal = ProposalLearningUnitFactory(state=proposal_state.ProposalState.ACCEPTED.name,
                                                        type=proposal_type.ProposalType.CREATION.name)
        consolidate_proposal(creation_proposal)

        self.assertFalse(ProposalLearningUnit.objects.filter(pk=creation_proposal.pk).exists())

        self.assertTrue(mock_edit_lu_end_date.called)
        lu_arg, academic_year_arg = mock_edit_lu_end_date.call_args[0]
        self.assertEqual(lu_arg.end_year, creation_proposal.learning_unit_year.academic_year.year)
        self.assertIsNone(academic_year_arg)

    @mock.patch("base.business.learning_unit_proposal.edit_learning_unit_end_date")
    def test_when_proposal_of_type_suppression_and_accepted(self, mock_edit_lu_end_date):
        academic_years = create_academic_years()
        initial_end_year_index = 2
        suppression_proposal = ProposalLearningUnitFactory(
            state=proposal_state.ProposalState.ACCEPTED.name,
            type=proposal_type.ProposalType.SUPPRESSION.name,
            initial_data={
                "learning_unit": {
                    "end_year": academic_years[initial_end_year_index].year
                }
            })
        random_end_acad_year_index = fuzzy.FuzzyInteger(initial_end_year_index+1, len(academic_years)-1).fuzz()
        suppression_proposal.learning_unit_year.learning_unit.end_year = academic_years[random_end_acad_year_index].year
        suppression_proposal.learning_unit_year.learning_unit.save()
        consolidate_proposal(suppression_proposal)

        self.assertFalse(ProposalLearningUnit.objects.filter(pk=suppression_proposal.pk).exists())

        self.assertTrue(mock_edit_lu_end_date.called)

        lu_arg, academic_year_arg = mock_edit_lu_end_date.call_args[0]
        self.assertEqual(lu_arg.end_year, suppression_proposal.initial_data["learning_unit"]["end_year"])
        suppression_proposal.learning_unit_year.learning_unit.refresh_from_db()
        self.assertEqual(academic_year_arg.year, suppression_proposal.learning_unit_year.learning_unit.end_year)

    @mock.patch("base.business.learning_unit_proposal.update_learning_unit_year_with_report")
    def test_when_proposal_of_type_modification_and_accepted(self, mock_update_learning_unit_with_report):
        generatorContainer = GenerateContainer(datetime.date.today().year-2, datetime.date.today().year)
        proposal = ProposalLearningUnitFactory(
            state=proposal_state.ProposalState.ACCEPTED.name,
            type=proposal_type.ProposalType.MODIFICATION.name,
            learning_unit_year=generatorContainer.generated_container_years[0].learning_unit_year_full,
            initial_data={
                "learning_unit": {},
                "learning_unit_year": {},
                "learning_container_year": {}
            }
        )

        consolidate_proposal(proposal)
        self.assertTrue(mock_update_learning_unit_with_report.called)


class TestModifyProposalState(TestCase):
    def test_change_new_state(self):
        proposal = ProposalLearningUnitFactory(state=proposal_state.ProposalState.FACULTY.name)
        new_state = proposal_state.ProposalState.SUSPENDED.name
        modify_proposal_state(new_state, proposal)

        proposal.refresh_from_db()
        self.assertEqual(proposal.state, new_state)
