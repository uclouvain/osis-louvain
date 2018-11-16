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

from django.contrib.auth.models import Permission, Group
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from base.business.learning_units import perms
from base.business.learning_units.perms import is_eligible_to_create_modification_proposal, \
    FACULTY_UPDATABLE_CONTAINER_TYPES, is_eligible_to_consolidate_proposal, is_academic_year_in_range_to_create_partim
from base.models.academic_year import AcademicYear, LEARNING_UNIT_CREATION_SPAN_YEARS, MAX_ACADEMIC_YEAR_FACULTY, \
    MAX_ACADEMIC_YEAR_CENTRAL
from base.models.enums import entity_container_year_link_type
from base.models.enums import proposal_state, proposal_type, learning_container_year_types
from base.models.enums.attribution_procedure import EXTERNAL
from base.models.enums.learning_container_year_types import OTHER_COLLECTIVE, OTHER_INDIVIDUAL, MASTER_THESIS, COURSE
from base.models.enums.learning_unit_year_subtypes import FULL, PARTIM
from base.models.enums.proposal_type import ProposalType
from base.models.person import FACULTY_MANAGER_GROUP, CENTRAL_MANAGER_GROUP, Person
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.business.learning_units import GenerateContainer, GenerateAcademicYear
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory, LearningUnitYearFakerFactory
from base.tests.factories.person import PersonFactory, FacultyManagerFactory, CentralManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.user import UserFactory

TYPES_PROPOSAL_NEEDED_TO_EDIT = (learning_container_year_types.COURSE,
                                 learning_container_year_types.DISSERTATION,
                                 learning_container_year_types.INTERNSHIP)

TYPES_DIRECT_EDIT_PERMITTED = (learning_container_year_types.OTHER_COLLECTIVE,
                               learning_container_year_types.OTHER_INDIVIDUAL,
                               learning_container_year_types.MASTER_THESIS,
                               learning_container_year_types.EXTERNAL)

ALL_TYPES = TYPES_PROPOSAL_NEEDED_TO_EDIT + TYPES_DIRECT_EDIT_PERMITTED


class PermsTestCase(TestCase):
    def setUp(self):
        today = datetime.date.today()
        self.academic_yr = AcademicYearFactory(start_date=today,
                                               end_date=today.replace(year=today.year + 1),
                                               year=today.year)
        self.academic_yr_1 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 1),
                                                       end_date=today.replace(year=today.year + 2),
                                                       year=today.year + 1)
        super(AcademicYear, self.academic_yr_1).save()
        self.academic_year_6 = AcademicYearFactory.build(start_date=today.replace(year=today.year + 6),
                                                         end_date=today.replace(year=today.year + 7),
                                                         year=today.year + 6)
        super(AcademicYear, self.academic_year_6).save()

        self.lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_yr)
        lu = LearningUnitFactory(end_year=self.academic_yr.year)
        self.luy = LearningUnitYearFactory(academic_year=self.academic_yr,
                                           learning_container_year=self.lunit_container_yr,
                                           subtype=FULL,
                                           learning_unit=lu)

    def test_can_faculty_manager_modify_end_date_partim(self):
        for container_type in ALL_TYPES:
            lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_yr,
                                                              container_type=container_type)
            luy = LearningUnitYearFactory(academic_year=self.academic_yr,
                                          learning_container_year=lunit_container_yr,
                                          subtype=PARTIM)

            self.assertTrue(luy.can_update_by_faculty_manager())

    def test_can_faculty_manager_modify_end_date_full(self):
        for direct_edit_permitted_container_type in TYPES_DIRECT_EDIT_PERMITTED:
            lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_yr,
                                                              container_type=direct_edit_permitted_container_type)
            luy = LearningUnitYearFactory(academic_year=self.academic_yr,
                                          learning_container_year=lunit_container_yr,
                                          subtype=FULL)

            self.assertTrue(luy.can_update_by_faculty_manager())

    def test_cannot_faculty_manager_modify_end_date_full(self):
        for proposal_needed_container_type in TYPES_PROPOSAL_NEEDED_TO_EDIT:
            lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_yr,
                                                              container_type=proposal_needed_container_type)
            luy = LearningUnitYearFactory(academic_year=self.academic_yr,
                                          learning_container_year=lunit_container_yr,
                                          subtype=FULL)

            self.assertFalse(perms.is_eligible_for_modification_end_date(luy,
                                                                         self.create_person_with_permission_and_group(
                                                                             FACULTY_MANAGER_GROUP)))

    def test_cannot_faculty_manager_modify_full(self):
        for proposal_needed_container_type in TYPES_PROPOSAL_NEEDED_TO_EDIT:
            lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_year_6,
                                                              container_type=proposal_needed_container_type)
            luy = LearningUnitYearFactory(academic_year=self.academic_year_6,
                                          learning_container_year=lunit_container_yr,
                                          subtype=FULL)

            self.assertFalse(perms.is_eligible_for_modification(luy, self.create_person_with_permission_and_group(
                FACULTY_MANAGER_GROUP)))

    def test_when_existing_proposal_in_epc(self):
        luy = LearningUnitYearFactory(academic_year=self.academic_yr, learning_unit__existing_proposal_in_epc=True)
        self.assertFalse(perms.is_eligible_for_modification(luy, None))
        self.assertFalse(perms.is_eligible_for_modification_end_date(luy, None))
        self.assertFalse(perms.is_eligible_to_create_partim(luy, None))
        self.assertFalse(perms.is_eligible_to_create_modification_proposal(luy, None))
        self.assertFalse(perms.is_eligible_to_delete_learning_unit_year(luy, None))

    def test_cannot_faculty_manager_modify_end_date_no_container(self):
        luy = LearningUnitYearFactory(academic_year=self.academic_yr,
                                      learning_container_year=None)
        self.assertFalse(luy.can_update_by_faculty_manager())

    def test_can_central_manager_modify_end_date_full(self):
        a_person = self.create_person_with_permission_and_group(CENTRAL_MANAGER_GROUP)
        generated_container = GenerateContainer(start_year=self.academic_yr.year,
                                                end_year=self.academic_yr.year)
        generated_container_first_year = generated_container.generated_container_years[0]
        luy = generated_container_first_year.learning_unit_year_full
        requirement_entity = generated_container_first_year.requirement_entity_container_year.entity
        PersonEntityFactory(entity=requirement_entity, person=a_person)
        for proposal_needed_container_type in ALL_TYPES:
            self.lunit_container_yr.container_type = proposal_needed_container_type
            self.lunit_container_yr.save()
            self.assertTrue(perms.is_eligible_for_modification_end_date(luy, a_person))

    def test_access_edit_learning_unit_proposal_as_central_manager(self):
        a_person = self.create_person_with_permission_and_group(CENTRAL_MANAGER_GROUP)
        generated_container = GenerateContainer(start_year=self.academic_yr.year,
                                                end_year=self.academic_yr.year)
        generated_container_first_year = generated_container.generated_container_years[0]
        luy = generated_container_first_year.learning_unit_year_full
        requirement_entity = generated_container_first_year.requirement_entity_container_year.entity
        PersonEntityFactory(entity=requirement_entity, person=a_person)

        self.assertFalse(perms.is_eligible_to_edit_proposal(None, a_person))

        a_proposal = ProposalLearningUnitFactory(learning_unit_year=luy)
        self.assertTrue(perms.is_eligible_to_edit_proposal(a_proposal, a_person))

    def test_access_edit_learning_unit_proposal_of_current_academic_year_as_faculty_manager(self):
        a_person = self.create_person_with_permission_and_group(FACULTY_MANAGER_GROUP)
        generated_container = GenerateContainer(start_year=self.academic_yr.year,
                                                end_year=self.academic_yr.year)
        generated_container_first_year = generated_container.generated_container_years[0]
        luy = generated_container_first_year.learning_unit_year_full
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year.entity
        PersonEntityFactory(entity=an_requirement_entity, person=a_person)
        a_proposal = ProposalLearningUnitFactory(learning_unit_year=luy,
                                                 type=proposal_type.ProposalType.MODIFICATION.name,
                                                 state=proposal_state.ProposalState.FACULTY.name)
        self.assertFalse(perms.is_eligible_to_edit_proposal(a_proposal, a_person))

    def test_access_edit_learning_unit_proposal_as_faculty_manager(self):
        generated_container = GenerateContainer(start_year=self.academic_yr_1.year,
                                                end_year=self.academic_yr_1.year)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year.entity

        luy = generated_container_first_year.learning_unit_year_full
        a_person = self.create_person_with_permission_and_group(FACULTY_MANAGER_GROUP)

        a_proposal = ProposalLearningUnitFactory(
            state=proposal_state.ProposalState.CENTRAL.name,
            type=proposal_type.ProposalType.SUPPRESSION.name,
            learning_unit_year=luy
        )

        PersonEntityFactory(entity=an_requirement_entity, person=a_person)

        self.assertFalse(perms.is_eligible_to_edit_proposal(None, a_person))

        self.assertFalse(perms.is_eligible_to_edit_proposal(a_proposal, a_person))

        self.assertFalse(perms.is_eligible_to_edit_proposal(a_proposal, a_person))

        a_proposal.state = proposal_state.ProposalState.CENTRAL.name
        a_proposal.save()
        self.assertFalse(perms.is_eligible_to_edit_proposal(a_proposal, a_person))

        a_proposal.state = proposal_state.ProposalState.FACULTY.name
        a_proposal.save()
        self.assertTrue(perms.is_eligible_to_edit_proposal(a_proposal, a_person))

        for tag in ProposalType.choices():
            a_proposal.type = tag[0]
            a_proposal.save()
            if a_proposal.type != ProposalType.MODIFICATION:
                self.assertTrue(perms.is_eligible_to_edit_proposal(a_proposal, a_person))
            else:
                self.assertFalse(perms.is_eligible_to_edit_proposal(a_proposal, a_person))

    def test_is_not_eligible_for_cancel_of_proposal(self):
        luy = LearningUnitYearFactory(academic_year=self.academic_yr)
        an_entity_container_year = EntityContainerYearFactory(
            learning_container_year=luy.learning_container_year,
            type=entity_container_year_link_type.REQUIREMENT_ENTITY
        )
        a_person = self.create_person_with_permission_and_group()
        a_proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.SUPPRESSION.name,
            state=proposal_state.ProposalState.CENTRAL.name,
            initial_data={
                "entities": {
                    entity_container_year_link_type.REQUIREMENT_ENTITY: an_entity_container_year.entity.id,
                }
            })
        self.assertFalse(perms.is_eligible_for_cancel_of_proposal(a_proposal, a_person))
        a_proposal.state = proposal_state.ProposalState.FACULTY.name
        a_proposal.save()
        self.assertFalse(perms.is_eligible_for_cancel_of_proposal(a_proposal, a_person))
        a_proposal.type = proposal_type.ProposalType.MODIFICATION.name
        a_proposal.save()
        self.assertFalse(perms.is_eligible_for_cancel_of_proposal(a_proposal, a_person))

    def test_is_eligible_for_cancel_of_proposal_for_creation(self):
        generated_container = GenerateContainer(start_year=self.academic_yr.year,
                                                end_year=self.academic_yr.year)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year.entity

        luy = generated_container_first_year.learning_unit_year_full
        a_person = self.create_person_with_permission_and_group(FACULTY_MANAGER_GROUP,
                                                                'can_propose_learningunit')

        a_proposal = ProposalLearningUnitFactory(learning_unit_year=luy,
                                                 type=proposal_type.ProposalType.CREATION.name,
                                                 state=proposal_state.ProposalState.FACULTY.name)

        PersonEntityFactory(person=a_person, entity=an_requirement_entity)
        self.assertTrue(perms.is_eligible_for_cancel_of_proposal(a_proposal, a_person))

    def test_is_eligible_for_cancel_of_proposal(self):
        generated_container = GenerateContainer(start_year=self.academic_yr.year,
                                                end_year=self.academic_yr.year)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year.entity

        luy = generated_container_first_year.learning_unit_year_full
        a_person = self.create_person_with_permission_and_group(FACULTY_MANAGER_GROUP,
                                                                'can_propose_learningunit')

        a_proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.MODIFICATION.name,
            state=proposal_state.ProposalState.FACULTY.name,
            initial_data={
                "entities": {
                    entity_container_year_link_type.REQUIREMENT_ENTITY: an_requirement_entity.id,
                }
            })

        PersonEntityFactory(person=a_person, entity=an_requirement_entity)
        self.assertTrue(perms.is_eligible_for_cancel_of_proposal(a_proposal, a_person))

    def test_is_eligible_for_cancel_of_proposal_wrong_state(self):
        generated_container = GenerateContainer(start_year=self.academic_yr.year,
                                                end_year=self.academic_yr.year)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year.entity

        luy = generated_container_first_year.learning_unit_year_full
        a_person = self.create_person_with_permission_and_group(FACULTY_MANAGER_GROUP,
                                                                'can_propose_learningunit')

        a_proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.MODIFICATION.name,
            state=proposal_state.ProposalState.CENTRAL.name,
            initial_data={
                "entities": {
                    entity_container_year_link_type.REQUIREMENT_ENTITY: an_requirement_entity.id,
                }
            })

        PersonEntityFactory(person=a_person, entity=an_requirement_entity)
        self.assertFalse(perms.is_eligible_for_cancel_of_proposal(a_proposal, a_person))

    def test_is_eligible_for_cancel_of_proposal_as_central_manager(self):
        generated_container = GenerateContainer(start_year=self.academic_yr.year,
                                                end_year=self.academic_yr.year)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year.entity

        luy = generated_container_first_year.learning_unit_year_full
        a_person = self.create_person_with_permission_and_group(CENTRAL_MANAGER_GROUP,
                                                                'can_propose_learningunit')

        a_proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.MODIFICATION.name,
            state=proposal_state.ProposalState.CENTRAL.name,
            initial_data={
                "entities": {
                    entity_container_year_link_type.REQUIREMENT_ENTITY: an_requirement_entity.id,
                }
            })
        PersonEntityFactory(person=a_person, entity=an_requirement_entity)
        self.assertTrue(perms.is_eligible_for_cancel_of_proposal(a_proposal, a_person))

    @staticmethod
    def create_person_with_permission_and_group(group_name=None, permission_name='can_edit_learning_unit_proposal'):
        a_user = UserFactory()
        permission, created = Permission.objects.get_or_create(
            codename=permission_name, content_type=ContentType.objects.get_for_model(ProposalLearningUnit))
        a_user.user_permissions.add(permission)
        a_person = PersonFactory(user=a_user)
        if group_name:
            a_person.user.groups.add(Group.objects.get(name=group_name))
        return a_person


class TestIsEligibleToCreateModificationProposal(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.past_academic_year = AcademicYearFactory(
            start_date=cls.current_academic_year.start_date - datetime.timedelta(days=365),
            end_date=cls.current_academic_year.end_date - datetime.timedelta(days=365),
            year=cls.current_academic_year.year - 1
        )
        cls.person = PersonFactory()

    def setUp(self):
        self.luy = LearningUnitYearFakerFactory(learning_container_year__academic_year=self.current_academic_year,
                                                learning_container_year__container_type=COURSE,
                                                subtype=FULL)
        self.entity_container_year = EntityContainerYearFactory(
            learning_container_year=self.luy.learning_container_year,
            type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        self.person_entity = PersonEntityFactory(person=self.person, entity=self.entity_container_year.entity)

    def test_cannot_propose_modification_of_past_learning_unit(self):
        past_luy = LearningUnitYearFakerFactory(learning_container_year__academic_year=self.past_academic_year)

        self.assertFalse(is_eligible_to_create_modification_proposal(past_luy, self.person))

    def test_cannot_propose_modification_of_partim(self):
        self.luy.subtype = PARTIM
        self.luy.save()

        self.assertFalse(is_eligible_to_create_modification_proposal(self.luy, self.person))

    def test_can_only_propose_modification_for_course_internship_and_dissertation(self):
        other_types = (OTHER_COLLECTIVE, OTHER_INDIVIDUAL, MASTER_THESIS, EXTERNAL)
        for luy_container_type in other_types:
            with self.subTest(luy_container_type=luy_container_type):
                self.luy.learning_container_year.container_type = luy_container_type
                self.luy.learning_container_year.save()
                self.assertFalse(is_eligible_to_create_modification_proposal(self.luy, self.person))

    def test_can_only_propose_modification_for_luy_which_is_not_currently_in_proposition(self):
        ProposalLearningUnitFactory(learning_unit_year=self.luy)

        self.assertFalse(is_eligible_to_create_modification_proposal(self.luy, self.person))

    def test_can_only_propose_modification_for_lu_which_is_not_in_proposition_on_different_year(self):
        past_luy_with_proposal = LearningUnitYearFakerFactory(
            learning_container_year__academic_year=self.past_academic_year,
            learning_unit=self.luy.learning_unit
        )
        ProposalLearningUnitFactory(learning_unit_year=past_luy_with_proposal)

        self.assertFalse(is_eligible_to_create_modification_proposal(self.luy, self.person))

    def test_cannot_propose_modification_for_luy_for_which_person_is_not_linked_to_entity(self):
        self.person_entity.delete()

        self.assertFalse(is_eligible_to_create_modification_proposal(self.luy, self.person))

    def test_all_requirements_are_met_to_propose_modification(self):
        for luy_container_type in FACULTY_UPDATABLE_CONTAINER_TYPES:
            with self.subTest(luy_container_type=luy_container_type):
                self.luy.learning_container_year.container_type = luy_container_type
                self.luy.learning_container_year.save()
                self.assertTrue(is_eligible_to_create_modification_proposal(self.luy, self.person))


class TestIsEligibleToConsolidateLearningUnitProposal(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.person_with_right_to_consolidate = PersonFactory()
        cls.person_with_right_to_consolidate.user.user_permissions.add(
            Permission.objects.get(codename="can_consolidate_learningunit_proposal")
        )

        cls.person_without_right_to_consolidate = PersonFactory()

    def test_when_person_has_no_right_to_consolidate(self):
        proposal_in_state_accepted = ProposalLearningUnitFactory(state=proposal_state.ProposalState.ACCEPTED.name)
        self.assertFalse(is_eligible_to_consolidate_proposal(proposal_in_state_accepted,
                                                             self.person_without_right_to_consolidate))

    def test_when_person_has_right_to_consolidate_but_proposal_state_is_neither_accepted_nor_refused(self):
        states = (state.name for state in proposal_state.ProposalState
                  if state not in (proposal_state.ProposalState.ACCEPTED, proposal_state.ProposalState.REFUSED))
        for state in states:
            with self.subTest(state=state):
                proposal = ProposalLearningUnitFactory(state=state)
                self.assertFalse(is_eligible_to_consolidate_proposal(proposal, self.person_with_right_to_consolidate))

    def test_when_person_not_linked_to_entity(self):
        proposal = ProposalLearningUnitFactory(state=proposal_state.ProposalState.ACCEPTED.name)
        self.assertFalse(is_eligible_to_consolidate_proposal(proposal, self.person_with_right_to_consolidate))

    def test_when_person_is_linked_to_entity(self):
        states = (state.name for state in proposal_state.ProposalState
                  if state in (proposal_state.ProposalState.ACCEPTED, proposal_state.ProposalState.REFUSED))

        for state in states:
            with self.subTest(state=state):
                proposal = ProposalLearningUnitFactory(state=state)
                entity_container = EntityContainerYearFactory(
                    learning_container_year=proposal.learning_unit_year.learning_container_year,
                    type=entity_container_year_link_type.REQUIREMENT_ENTITY
                )

                PersonEntityFactory(person=self.person_with_right_to_consolidate,
                                    entity=entity_container.entity)
                # Refresh permissions
                self.person_with_right_to_consolidate = Person.objects.get(pk=self.person_with_right_to_consolidate.pk)

                self.assertTrue(is_eligible_to_consolidate_proposal(proposal, self.person_with_right_to_consolidate))


class TestIsAcademicYearInRangeToCreatePartim(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_acy = create_current_academic_year()
        cls.academic_years = GenerateAcademicYear(
            cls.current_acy.year - LEARNING_UNIT_CREATION_SPAN_YEARS,
            cls.current_acy.year + LEARNING_UNIT_CREATION_SPAN_YEARS
        ).academic_years
        cls.academic_years[LEARNING_UNIT_CREATION_SPAN_YEARS] = cls.current_acy
        cls.learning_unit_years = [LearningUnitYearFactory(academic_year=acy) for acy in cls.academic_years]

        cls.faculty_manager = FacultyManagerFactory()
        cls.central_manager = CentralManagerFactory()

    def test_for_faculty_manager(self):
        self._test_can_create_partim_based_on_person(self.faculty_manager, MAX_ACADEMIC_YEAR_FACULTY)

    def test_for_central_manager(self):
        self._test_can_create_partim_based_on_person(self.central_manager, MAX_ACADEMIC_YEAR_CENTRAL)

    def _test_can_create_partim_based_on_person(self, person, max_range):
        for luy in self.learning_unit_years:
            with self.subTest(academic_year=luy.academic_year):
                if self.current_acy.year <= luy.academic_year.year <= self.current_acy.year + max_range:
                    self.assertTrue(is_academic_year_in_range_to_create_partim(luy, person))
                else:
                    self.assertFalse(is_academic_year_in_range_to_create_partim(luy, person))
