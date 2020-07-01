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
from unittest import mock

from django.contrib.auth.models import Permission
from django.test import TestCase

from attribution.tests.factories.tutor_application import TutorApplicationFactory
from base.business.learning_units import perms
from base.business.learning_units.perms import is_eligible_to_create_modification_proposal, \
    FACULTY_UPDATABLE_CONTAINER_TYPES, is_eligible_to_consolidate_proposal, _check_proposal_edition
from base.business.perms import view_academicactors
from base.models.academic_year import AcademicYear, LEARNING_UNIT_CREATION_SPAN_YEARS, MAX_ACADEMIC_YEAR_FACULTY, \
    MAX_ACADEMIC_YEAR_CENTRAL
from base.models.enums import proposal_state, proposal_type, learning_container_year_types, learning_unit_year_subtypes
from base.models.enums.attribution_procedure import EXTERNAL
from base.models.enums.groups import CENTRAL_MANAGER_GROUP, FACULTY_MANAGER_GROUP, UE_FACULTY_MANAGER_GROUP
from base.models.enums.learning_container_year_types import OTHER_COLLECTIVE, OTHER_INDIVIDUAL, MASTER_THESIS, COURSE
from base.models.enums.learning_unit_year_subtypes import FULL, PARTIM
from base.models.enums.proposal_state import ProposalState
from base.models.enums.proposal_type import ProposalType
from base.models.person import Person
from base.tests.factories.academic_calendar import generate_modification_transformation_proposal_calendars, \
    generate_learning_unit_edition_calendars
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year, \
    create_past_academic_year
from base.tests.factories.business.learning_units import GenerateContainer, GenerateAcademicYear
from base.tests.factories.entity import EntityFactory
from base.tests.factories.external_learning_unit_year import ExternalLearningUnitYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory, LearningUnitYearFakerFactory
from base.tests.factories.person import PersonFactory, CentralManagerForUEFactory, \
    PersonWithPermissionsFactory, FacultyManagerForUEFactory
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
    @classmethod
    def setUpTestData(cls):
        cls.person_fac = FacultyManagerForUEFactory()
        cls.academic_yr = create_current_academic_year()
        cls.academic_yr_1 = AcademicYearFactory.build(year=cls.academic_yr.year + 1)
        super(AcademicYear, cls.academic_yr_1).save()
        cls.academic_yr_2 = AcademicYearFactory.build(year=cls.academic_yr.year + 2)
        super(AcademicYear, cls.academic_yr_2).save()
        cls.academic_yr_6 = AcademicYearFactory.build(year=cls.academic_yr.year + 6)
        super(AcademicYear, cls.academic_yr_6).save()
        previous_academic_yr = AcademicYearFactory.build(year=cls.academic_yr.year - 1)
        super(AcademicYear, previous_academic_yr).save()

        cls.lunit_container_yr = LearningContainerYearFactory(academic_year=cls.academic_yr)
        cls.luy = LearningUnitYearFactory(
            academic_year=cls.academic_yr,
            learning_container_year=cls.lunit_container_yr,
            subtype=FULL,
            learning_unit=LearningUnitFactory(start_year=create_past_academic_year(), end_year=cls.academic_yr)
        )
        academic_years = [cls.academic_yr, cls.academic_yr_1, cls.academic_yr_2]
        generate_learning_unit_edition_calendars(academic_years)

    def test_can_faculty_manager_modify_end_date_partim(self):
        for container_type in ALL_TYPES:
            lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_yr,
                                                              container_type=container_type)
            luy = LearningUnitYearFactory(academic_year=self.academic_yr,
                                          learning_container_year=lunit_container_yr,
                                          subtype=PARTIM)

            self.assertTrue(perms._is_learning_unit_year_in_state_to_be_modified(luy, self.person_fac, False))

    def test_not_eligible_if_has_application(self):
        luy = LearningUnitYearFactory(academic_year__year=2020)
        TutorApplicationFactory(learning_container_year=luy.learning_container_year)
        self.assertFalse(
            perms.is_eligible_for_modification_end_date(
                luy, PersonWithPermissionsFactory('can_edit_learningunit_date')
            )
        )

    def test_can_faculty_manager_modify_end_date_full(self):
        for direct_edit_permitted_container_type in TYPES_DIRECT_EDIT_PERMITTED:
            lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_yr,
                                                              container_type=direct_edit_permitted_container_type)
            luy = LearningUnitYearFactory(academic_year=self.academic_yr,
                                          learning_container_year=lunit_container_yr,
                                          subtype=FULL)

            self.assertTrue(perms._is_learning_unit_year_in_state_to_be_modified(luy, self.person_fac, False))

    def test_cannot_faculty_manager_modify_end_date_full(self):
        for proposal_needed_container_type in TYPES_PROPOSAL_NEEDED_TO_EDIT:
            lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_yr,
                                                              container_type=proposal_needed_container_type)
            luy = LearningUnitYearFactory(academic_year=self.academic_yr,
                                          learning_container_year=lunit_container_yr,
                                          subtype=FULL)

            self.assertFalse(perms.is_eligible_for_modification_end_date(luy,
                                                                         create_person_with_permission_and_group(
                                                                             FACULTY_MANAGER_GROUP)))
            self.assertFalse(perms.is_eligible_for_modification_end_date(
                luy,
                create_person_with_permission_and_group(UE_FACULTY_MANAGER_GROUP)
            ))

    def test_cannot_faculty_manager_modify_full(self):
        for proposal_needed_container_type in TYPES_PROPOSAL_NEEDED_TO_EDIT:
            lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_yr_6,
                                                              container_type=proposal_needed_container_type)
            luy = LearningUnitYearFactory(academic_year=self.academic_yr_6,
                                          learning_container_year=lunit_container_yr,
                                          subtype=FULL)

            self.assertFalse(perms.is_eligible_for_modification(luy, create_person_with_permission_and_group(
                FACULTY_MANAGER_GROUP)))
            self.assertFalse(perms.is_eligible_for_modification(
                luy,
                create_person_with_permission_and_group(UE_FACULTY_MANAGER_GROUP)
            ))

    @mock.patch('base.business.learning_units.perms.is_year_editable')
    @mock.patch('base.business.learning_units.perms._is_learning_unit_year_in_state_to_be_modified')
    @mock.patch('base.business.learning_units.perms.is_person_linked_to_entity_in_charge_of_lu')
    def test_when_external_learning_unit_is_not_co_graduation(
            self,
            mock_is_person_linked_to_entity_in_charge_of_lu,
            mock_is_learning_unit_year_in_state_to_be_modified,
            mock_is_year_editable):
        mock_is_person_linked_to_entity_in_charge_of_lu.return_value = True
        mock_is_learning_unit_year_in_state_to_be_modified.return_value = True
        mock_is_year_editable.return_value = True
        a_person = CentralManagerForUEFactory()
        luy = LearningUnitYearFactory(academic_year=self.academic_yr)
        ExternalLearningUnitYearFactory(learning_unit_year=luy, co_graduation=False)
        self.assertFalse(perms.is_external_learning_unit_cograduation(luy, a_person, False))

    def test_when_learning_unit_is_not_external(self):
        learning_unit_year = LearningUnitYearFactory()
        person = PersonFactory()
        self.assertTrue(perms.is_external_learning_unit_cograduation(learning_unit_year, person, False))

    def test_cannot_faculty_manager_modify_end_date_no_container(self):
        luy = LearningUnitYearFactory(academic_year=self.academic_yr,
                                      learning_container_year=None)
        self.assertFalse(perms._is_learning_unit_year_in_state_to_be_modified(luy, self.person_fac, False))

    def test_can_central_manager_modify_end_date_full(self):
        a_person = create_person_with_permission_and_group(CENTRAL_MANAGER_GROUP, 'can_edit_learningunit')
        a_person.user.user_permissions.add(Permission.objects.get(codename='can_edit_learningunit_date'))
        generated_container = GenerateContainer(start_year=self.academic_yr,
                                                end_year=self.academic_yr)
        generated_container_first_year = generated_container.generated_container_years[0]
        luy = generated_container_first_year.learning_unit_year_full
        requirement_entity = generated_container_first_year.requirement_entity_container_year
        PersonEntityFactory(entity=requirement_entity, person=a_person)
        lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_yr)
        for proposal_needed_container_type in ALL_TYPES:
            lunit_container_yr.container_type = proposal_needed_container_type
            lunit_container_yr.save()
            self.assertTrue(perms.is_eligible_for_modification_end_date(luy, a_person))

    def test_access_edit_learning_unit_proposal_as_central_manager(self):
        a_person = create_person_with_permission_and_group(CENTRAL_MANAGER_GROUP)
        generated_container = GenerateContainer(start_year=self.academic_yr,
                                                end_year=self.academic_yr)
        generated_container_first_year = generated_container.generated_container_years[0]
        luy = generated_container_first_year.learning_unit_year_full
        requirement_entity = generated_container_first_year.requirement_entity_container_year
        PersonEntityFactory(entity=requirement_entity, person=a_person)

        self.assertFalse(perms.is_eligible_to_edit_proposal(None, a_person))

        a_proposal = ProposalLearningUnitFactory(learning_unit_year=luy)
        self.assertTrue(perms.is_eligible_to_edit_proposal(a_proposal, a_person))

    def test_access_edit_learning_unit_proposal_of_current_academic_year_as_faculty_manager(self):
        faculty_managers = [
            create_person_with_permission_and_group(FACULTY_MANAGER_GROUP),
            create_person_with_permission_and_group(UE_FACULTY_MANAGER_GROUP)
        ]
        generated_container = GenerateContainer(start_year=self.academic_yr,
                                                end_year=self.academic_yr)
        generated_container_first_year = generated_container.generated_container_years[0]
        luy = generated_container_first_year.learning_unit_year_full
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year
        a_proposal = ProposalLearningUnitFactory(learning_unit_year=luy,
                                                 type=proposal_type.ProposalType.MODIFICATION.name,
                                                 state=proposal_state.ProposalState.FACULTY.name)
        for manager in faculty_managers:
            PersonEntityFactory(entity=an_requirement_entity, person=manager)
            self.assertFalse(perms.is_eligible_to_edit_proposal(a_proposal, manager))

    def test_access_edit_learning_unit_proposal_as_faculty_manager(self):
        generated_container = GenerateContainer(start_year=self.academic_yr_1,
                                                end_year=self.academic_yr_1)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year

        luy = generated_container_first_year.learning_unit_year_full
        faculty_managers = [
            create_person_with_permission_and_group(FACULTY_MANAGER_GROUP),
            create_person_with_permission_and_group(UE_FACULTY_MANAGER_GROUP)
        ]

        a_proposal = ProposalLearningUnitFactory(
            state=proposal_state.ProposalState.CENTRAL.name,
            type=proposal_type.ProposalType.SUPPRESSION.name,
            learning_unit_year=luy
        )

        generate_modification_transformation_proposal_calendars(
            [self.academic_yr, self.academic_yr_1, self.academic_yr_2, self.academic_yr_6]
        )

        for manager in faculty_managers:
            a_proposal.state = proposal_state.ProposalState.CENTRAL.name
            a_proposal.save()
            PersonEntityFactory(entity=an_requirement_entity, person=manager)

            self.assertFalse(perms.is_eligible_to_edit_proposal(None, manager))
            self.assertFalse(perms.is_eligible_to_edit_proposal(a_proposal, manager))

            a_proposal.state = proposal_state.ProposalState.FACULTY.name
            a_proposal.save()
            self.assertTrue(perms.is_eligible_to_edit_proposal(a_proposal, manager))

            for tag in ProposalType.choices():
                a_proposal.type = tag[0]
                a_proposal.save()
                if a_proposal.type != ProposalType.MODIFICATION:
                    self.assertTrue(perms.is_eligible_to_edit_proposal(a_proposal, manager))
                else:
                    self.assertFalse(perms.is_eligible_to_edit_proposal(a_proposal, manager))

    def test_is_not_eligible_for_cancel_of_proposal(self):
        luy = LearningUnitYearFactory(academic_year=self.academic_yr)
        an_entity = EntityFactory()
        luy.learning_container_year.requirement_entity = an_entity
        luy.learning_container_year.save()
        a_person = create_person_with_permission_and_group()
        a_proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.SUPPRESSION.name,
            state=proposal_state.ProposalState.CENTRAL.name,
            initial_data={
                "learning_container_year": {
                    "requirement_entity": an_entity.id,
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
        generated_container = GenerateContainer(start_year=self.academic_yr,
                                                end_year=self.academic_yr)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year

        luy = generated_container_first_year.learning_unit_year_full

        faculty_managers = [
            create_person_with_permission_and_group(FACULTY_MANAGER_GROUP, 'can_propose_learningunit'),
            create_person_with_permission_and_group(UE_FACULTY_MANAGER_GROUP, 'can_propose_learningunit')
        ]

        a_proposal = ProposalLearningUnitFactory(learning_unit_year=luy,
                                                 type=proposal_type.ProposalType.CREATION.name,
                                                 state=proposal_state.ProposalState.FACULTY.name)

        for manager in faculty_managers:
            PersonEntityFactory(person=manager, entity=an_requirement_entity)
            self.assertTrue(perms.is_eligible_for_cancel_of_proposal(a_proposal, manager))

    def test_is_eligible_for_cancel_of_proposal(self):
        generated_container = GenerateContainer(start_year=self.academic_yr, end_year=self.academic_yr)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year

        luy = generated_container_first_year.learning_unit_year_full

        faculty_managers = [
            create_person_with_permission_and_group(FACULTY_MANAGER_GROUP, 'can_propose_learningunit'),
            create_person_with_permission_and_group(UE_FACULTY_MANAGER_GROUP, 'can_propose_learningunit')
        ]

        a_proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.MODIFICATION.name,
            state=proposal_state.ProposalState.FACULTY.name,
            initial_data={
                "learning_container_year": {
                    "requirement_entity": an_requirement_entity.id,
                }
            })

        for manager in faculty_managers:
            PersonEntityFactory(person=manager, entity=an_requirement_entity)
            self.assertTrue(perms.is_eligible_for_cancel_of_proposal(a_proposal, manager))

    def test_is_eligible_for_cancel_of_proposal_wrong_state(self):
        generated_container = GenerateContainer(start_year=self.academic_yr,
                                                end_year=self.academic_yr)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year

        luy = generated_container_first_year.learning_unit_year_full

        faculty_managers = [
            create_person_with_permission_and_group(FACULTY_MANAGER_GROUP, 'can_propose_learningunit'),
            create_person_with_permission_and_group(UE_FACULTY_MANAGER_GROUP, 'can_propose_learningunit')
        ]

        a_proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.MODIFICATION.name,
            state=proposal_state.ProposalState.CENTRAL.name,
            initial_data={
                "learning_container_year": {
                    "requirement_entity": an_requirement_entity.id,
                }
            })

        for manager in faculty_managers:
            PersonEntityFactory(person=manager, entity=an_requirement_entity)
            self.assertFalse(perms.is_eligible_for_cancel_of_proposal(a_proposal, manager))

    def test_is_eligible_for_cancel_of_proposal_as_central_manager(self):
        generated_container = GenerateContainer(start_year=self.academic_yr,
                                                end_year=self.academic_yr)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year

        luy = generated_container_first_year.learning_unit_year_full
        a_person = create_person_with_permission_and_group(CENTRAL_MANAGER_GROUP,
                                                           'can_propose_learningunit')

        a_proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.MODIFICATION.name,
            state=proposal_state.ProposalState.CENTRAL.name,
            initial_data={
                "learning_container_year": {
                    "requirement_entity": an_requirement_entity.id,
                }
            })
        PersonEntityFactory(person=a_person, entity=an_requirement_entity)
        self.assertTrue(perms.is_eligible_for_cancel_of_proposal(a_proposal, a_person))

    def test_is_learning_unit_year_in_state_to_be_modified(self):
        luy = LearningUnitYearFactory(
            acronym="LDROI1004",
            specific_title="Juridic law courses",
            academic_year=self.academic_yr,
            subtype=learning_unit_year_subtypes.FULL
        )
        start_year = AcademicYearFactory(year=self.academic_yr.year - 3)
        end_year = AcademicYearFactory(year=self.academic_yr.year - 1)
        previous_academic_years = GenerateAcademicYear(start_year=start_year, end_year=end_year).academic_years
        next_academic_years = GenerateAcademicYear(
            start_year=self.academic_yr_1, end_year=self.academic_yr_6).academic_years
        previous_luys = [LearningUnitYearFactory(academic_year=ac, learning_unit=luy.learning_unit)
                         for ac in previous_academic_years]
        next_luys = [LearningUnitYearFactory(academic_year=ac, learning_unit=luy.learning_unit)
                     for ac in next_academic_years]

        learning_units_can_be_modified = [luy, next_luys[0], next_luys[1]]
        for luy in learning_units_can_be_modified:
            with self.subTest(luy=luy):
                self.assertTrue(perms._is_learning_unit_year_in_state_to_be_modified(luy, self.person_fac, False))

        learning_units_cannot_be_modified = previous_luys + [next_luys[2], next_luys[3], next_luys[4]]
        for luy in learning_units_cannot_be_modified:
            with self.subTest(luy=luy):
                self.assertFalse(perms._is_learning_unit_year_in_state_to_be_modified(luy, self.person_fac, False))

    def test_is_not_eligible_if_creation_proposal_has_application(self):
        luy = LearningUnitYearFactory()
        proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=ProposalType.CREATION.name
        )
        TutorApplicationFactory(learning_container_year=luy.learning_container_year)

        self.assertFalse(
            perms.is_eligible_for_cancel_of_proposal(
                proposal, CentralManagerForUEFactory()
            )
        )


def create_person_with_permission_and_group(group_name=None, permission_name='can_edit_learning_unit_proposal'):
    return PersonWithPermissionsFactory(permission_name, groups=None if not group_name else [group_name])


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
        cls.person.user.user_permissions.add(
            Permission.objects.get(codename='can_propose_learningunit'),
        )

    def setUp(self):
        requirement_entity = EntityFactory()
        self.luy = LearningUnitYearFakerFactory(learning_container_year__academic_year=self.current_academic_year,
                                                learning_container_year__container_type=COURSE,
                                                subtype=FULL,
                                                learning_container_year__requirement_entity=requirement_entity)
        self.person_entity = PersonEntityFactory(person=self.person, entity=requirement_entity)

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

    def test_check_proposal_edition_ko(self):
        past_luy_with_proposal = LearningUnitYearFakerFactory(
            academic_year=self.past_academic_year,
            learning_container_year__academic_year=self.past_academic_year,
            learning_unit=self.luy.learning_unit
        )
        ProposalLearningUnitFactory(learning_unit_year=past_luy_with_proposal)

        self.assertFalse(_check_proposal_edition(
            self.luy,
            False)
        )

    def test_check_proposal_edition_ok(self):
        past_luy = LearningUnitYearFakerFactory(
            academic_year=self.past_academic_year,
            learning_container_year__academic_year=self.past_academic_year,
            learning_unit=self.luy.learning_unit
        )
        ProposalLearningUnitFactory(learning_unit_year=self.luy)

        self.assertTrue(_check_proposal_edition(
            past_luy,
            False)
        )


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
        proposal = ProposalLearningUnitFactory(
            state=proposal_state.ProposalState.ACCEPTED.name,
            learning_unit_year__learning_container_year__requirement_entity=EntityFactory(),
        )
        self.assertFalse(is_eligible_to_consolidate_proposal(proposal, self.person_with_right_to_consolidate))

    def test_when_person_is_linked_to_entity(self):
        states = (state.name for state in proposal_state.ProposalState
                  if state in (proposal_state.ProposalState.ACCEPTED, proposal_state.ProposalState.REFUSED))

        for state in states:
            with self.subTest(state=state):
                proposal = ProposalLearningUnitFactory(state=state)
                container_year = proposal.learning_unit_year.learning_container_year
                container_year.requirement_entity = EntityFactory()
                container_year.save()

                PersonEntityFactory(person=self.person_with_right_to_consolidate,
                                    entity=container_year.requirement_entity)
                # Refresh permissions
                self.person_with_right_to_consolidate = Person.objects.get(pk=self.person_with_right_to_consolidate.pk)

                self.assertTrue(is_eligible_to_consolidate_proposal(proposal, self.person_with_right_to_consolidate))

    def test_is_not_eligible_consolidate_delete_proposal_if_has_applications(self):
        requirement_entity = EntityFactory()
        luy = LearningUnitYearFactory(learning_container_year__requirement_entity=requirement_entity)
        proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=ProposalType.SUPPRESSION.name,
            state=ProposalState.ACCEPTED.name
        )
        TutorApplicationFactory(learning_container_year=luy.learning_container_year)
        person = PersonWithPermissionsFactory('can_consolidate_learningunit_proposal')
        PersonEntityFactory(person=person, entity=requirement_entity)
        self.assertFalse(
            perms.is_eligible_to_consolidate_proposal(
                proposal, person
            )
        )


class TestIsAcademicYearInRangeToCreatePartim(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_acy = create_current_academic_year()
        start_year = AcademicYearFactory(year=cls.current_acy.year - LEARNING_UNIT_CREATION_SPAN_YEARS)
        end_year = AcademicYearFactory(year=cls.current_acy.year + LEARNING_UNIT_CREATION_SPAN_YEARS)
        cls.generated_ac_years = GenerateAcademicYear(start_year, end_year)
        cls.academic_years = GenerateAcademicYear(start_year, end_year).academic_years
        cls.academic_years[LEARNING_UNIT_CREATION_SPAN_YEARS] = cls.current_acy
        cls.learning_unit_years = [LearningUnitYearFactory(academic_year=acy) for acy in cls.academic_years]
        generate_learning_unit_edition_calendars(cls.academic_years)

        cls.central_manager = CentralManagerForUEFactory()
        cls.faculty_manager_for_ue = FacultyManagerForUEFactory()

    def test_for_faculty_manager_for_ue(self):
        self._test_can_create_partim_based_on_person(self.faculty_manager_for_ue, MAX_ACADEMIC_YEAR_FACULTY)

    def test_for_central_manager(self):
        self._test_can_create_partim_based_on_person(self.central_manager, MAX_ACADEMIC_YEAR_CENTRAL)

    def _test_can_create_partim_based_on_person(self, person, max_range):
        for luy in self.learning_unit_years:
            with self.subTest(academic_year=luy.academic_year):
                if self.current_acy.year <= luy.academic_year.year <= self.current_acy.year + max_range:
                    self.assertTrue(perms._is_learning_unit_year_in_state_to_create_partim(luy, person))
                else:
                    self.assertFalse(perms._is_learning_unit_year_in_state_to_create_partim(luy, person))


class PermsViewAcademicActorCase(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_has_no_perms(self):
        self.assertFalse(view_academicactors(self.user))

    def test_has_valid_perms(self):
        self.user.user_permissions.add(Permission.objects.get(codename="view_programmanager"))
        self.user.refresh_from_db()
        self.assertTrue(view_academicactors(self.user))
