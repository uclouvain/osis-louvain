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
from types import SimpleNamespace
from unittest import mock

from django.contrib.auth.models import Permission
from django.test import TestCase

from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from attribution.tests.factories.tutor_application import TutorApplicationFactory
from base.business.perms import view_academicactors
from base.models.academic_year import AcademicYear, LEARNING_UNIT_CREATION_SPAN_YEARS, MAX_ACADEMIC_YEAR_FACULTY
from base.models.enums import proposal_state, proposal_type, learning_container_year_types, learning_unit_year_subtypes
from base.models.enums.attribution_procedure import EXTERNAL
from base.models.enums.learning_container_year_types import OTHER_COLLECTIVE, OTHER_INDIVIDUAL, MASTER_THESIS, COURSE
from base.models.enums.learning_unit_year_subtypes import FULL, PARTIM
from base.models.enums.proposal_state import ProposalState
from base.models.enums.proposal_type import ProposalType
from base.tests.factories.academic_calendar import generate_learning_unit_edition_calendars, \
    generate_proposal_calendars, generate_proposal_calendars_without_start_and_end_date
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year, \
    create_past_academic_year
from base.tests.factories.business.learning_units import GenerateContainer, GenerateAcademicYear
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.external_learning_unit_year import ExternalLearningUnitYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory, LearningUnitYearFakerFactory
from base.tests.factories.person import PersonFactory, CentralManagerForUEFactory, \
    PersonWithPermissionsFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.user import UserFactory
from learning_unit.auth import predicates
from learning_unit.auth.predicates import FACULTY_EDITABLE_CONTAINER_TYPES, FACULTY_DATE_EDITABLE_CONTAINER_TYPES
from learning_unit.tests.factories.central_manager import CentralManagerFactory
from learning_unit.tests.factories.faculty_manager import FacultyManagerFactory

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
        cls.academic_yr = create_current_academic_year()
        cls.academic_yr_1 = AcademicYearFactory.build(year=cls.academic_yr.year + 1)
        super(AcademicYear, cls.academic_yr_1).save()
        cls.academic_yr_2 = AcademicYearFactory.build(year=cls.academic_yr.year + 2)
        super(AcademicYear, cls.academic_yr_2).save()
        cls.academic_yr_6 = AcademicYearFactory.build(year=cls.academic_yr.year + 6)
        super(AcademicYear, cls.academic_yr_6).save()
        previous_academic_yr = AcademicYearFactory.build(year=cls.academic_yr.year - 1)
        super(AcademicYear, previous_academic_yr).save()

        cls.lunit_container_yr = LearningContainerYearFactory(
            academic_year=cls.academic_yr,
            requirement_entity=EntityFactory()
        )
        cls.luy = LearningUnitYearFactory(
            academic_year=cls.academic_yr,
            learning_container_year=cls.lunit_container_yr,
            subtype=FULL,
            learning_unit=LearningUnitFactory(start_year=create_past_academic_year(), end_year=cls.academic_yr)
        )
        cls.entity = cls.luy.learning_container_year.requirement_entity
        cls.faculty_manager = FacultyManagerFactory(entity=cls.entity)
        academic_years = [cls.academic_yr, cls.academic_yr_1, cls.academic_yr_2]
        generate_learning_unit_edition_calendars(academic_years)
        generate_proposal_calendars(academic_years)

    def test_can_faculty_manager_modify_end_date_partim(self):
        for container_type in [type.name for type in FACULTY_EDITABLE_CONTAINER_TYPES]:
            lunit_container_yr = LearningContainerYearFactory(
                academic_year=self.academic_yr,
                container_type=container_type,
                requirement_entity=self.entity
            )
            luy = LearningUnitYearFactory(
                academic_year=self.academic_yr,
                learning_container_year=lunit_container_yr,
                subtype=PARTIM
            )

            self.assertTrue(self.faculty_manager.person.user.has_perm('base.can_edit_learningunit_date', luy))

    def test_not_eligible_if_has_application_in_future(self):
        next_luy = LearningUnitYearFactory(
            learning_unit=self.luy.learning_unit,
            academic_year__year=self.luy.academic_year.year+1,
            learning_container_year__learning_container=self.luy.learning_container_year.learning_container
        )
        TutorApplicationFactory(learning_container_year=next_luy.learning_container_year)
        central_manager = CentralManagerFactory(entity=self.luy.learning_container_year.requirement_entity)
        self.assertFalse(central_manager.person.user.has_perm('base.can_edit_learningunit_date', self.luy))

    def test_eligible_if_has_application_but_none_in_future(self):
        TutorApplicationFactory(learning_container_year=self.luy.learning_container_year)
        central_manager = CentralManagerFactory(entity=self.luy.learning_container_year.requirement_entity)
        self.assertTrue(central_manager.person.user.has_perm('base.can_edit_learningunit_date', self.luy))

    def test_can_faculty_manager_modify_end_date_full(self):
        for direct_edit_permitted_container_type in [type.name for type in FACULTY_DATE_EDITABLE_CONTAINER_TYPES]:
            lunit_container_yr = LearningContainerYearFactory(
                academic_year=self.academic_yr,
                container_type=direct_edit_permitted_container_type,
                requirement_entity=self.entity
            )
            luy = LearningUnitYearFactory(
                academic_year=self.academic_yr,
                learning_container_year=lunit_container_yr,
                subtype=FULL
            )
            self.assertTrue(self.faculty_manager.person.user.has_perm('base.can_edit_learningunit_date', luy))

    def test_cannot_faculty_manager_modify_end_date_full(self):
        faculty_manager = FacultyManagerFactory()
        for proposal_needed_container_type in TYPES_PROPOSAL_NEEDED_TO_EDIT:
            lunit_container_yr = LearningContainerYearFactory(
                academic_year=self.academic_yr,
                container_type=proposal_needed_container_type
            )
            luy = LearningUnitYearFactory(
                academic_year=self.academic_yr,
                learning_container_year=lunit_container_yr,
                subtype=FULL
            )
            self.assertFalse(faculty_manager.person.user.has_perm('base.can_edit_learningunit_date', luy))

    def test_cannot_faculty_manager_modify_full(self):
        faculty_manager = FacultyManagerFactory()
        for proposal_needed_container_type in TYPES_PROPOSAL_NEEDED_TO_EDIT:
            lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_yr_6,
                                                              container_type=proposal_needed_container_type)
            luy = LearningUnitYearFactory(academic_year=self.academic_yr_6,
                                          learning_container_year=lunit_container_yr,
                                          subtype=FULL)

            self.assertFalse(faculty_manager.person.user.has_perm('base.can_edit_learningunit', luy))

    @mock.patch('learning_unit.auth.predicates.is_user_attached_to_current_requirement_entity')
    def test_when_external_learning_unit_is_not_co_graduation(self, mock_is_person_linked_to_entity_in_charge_of_lu):
        mock_is_person_linked_to_entity_in_charge_of_lu.return_value = True
        a_person = CentralManagerForUEFactory()
        luy = LearningUnitYearFactory(academic_year=self.academic_yr)
        ExternalLearningUnitYearFactory(learning_unit_year=luy, co_graduation=False)
        check_external = predicates.is_external_learning_unit_with_cograduation.__wrapped__
        mock_context = SimpleNamespace(context={'perm_name': 'undefined perm'})
        self.assertFalse(check_external(mock_context, a_person.user, luy))

    def test_when_learning_unit_is_not_external(self):
        learning_unit_year = LearningUnitYearFactory()
        person = PersonFactory()
        check_external = predicates.is_external_learning_unit_with_cograduation.__wrapped__
        mock_context = SimpleNamespace(context={'perm_name': 'undefined perm'})
        self.assertFalse(check_external(mock_context, person.user, learning_unit_year))

    def test_cannot_faculty_manager_modify_end_date_with_attributions_in_future(self):
        luy = LearningUnitYearFactory(academic_year=self.academic_yr)
        next_year_lu = LearningUnitYearFactory(learning_unit=luy.learning_unit, academic_year=self.academic_yr_1)
        AttributionChargeNewFactory(learning_component_year__learning_unit_year=next_year_lu)
        self.assertFalse(self.faculty_manager.person.user.has_perm('base.can_edit_learningunit_date', luy))

    def test_can_central_manager_modify_end_date_full(self):
        generated_container = GenerateContainer(start_year=self.academic_yr, end_year=self.academic_yr)
        generated_container_first_year = generated_container.generated_container_years[0]
        luy = generated_container_first_year.learning_unit_year_full
        requirement_entity = generated_container_first_year.requirement_entity_container_year
        central_manager = CentralManagerFactory(entity=requirement_entity)
        lunit_container_yr = LearningContainerYearFactory(academic_year=self.academic_yr)
        for proposal_needed_container_type in ALL_TYPES:
            lunit_container_yr.container_type = proposal_needed_container_type
            lunit_container_yr.save()
            self.assertTrue(central_manager.person.user.has_perm('base.can_edit_learningunit_date', luy))

    def test_cannot_access_edit_learning_unit_proposal_as_central_manager(self):
        generated_container = GenerateContainer(start_year=self.academic_yr, end_year=self.academic_yr)
        generated_container_first_year = generated_container.generated_container_years[0]
        luy = generated_container_first_year.learning_unit_year_full
        requirement_entity = generated_container_first_year.requirement_entity_container_year
        central_manager = CentralManagerFactory(entity=requirement_entity)
        self.assertFalse(central_manager.person.user.has_perm('base.can_edit_learning_unit_proposal', luy))

    def test_can_access_edit_learning_unit_proposal_as_central_manager(self):
        generated_container = GenerateContainer(start_year=self.academic_yr, end_year=self.academic_yr)
        generated_container_first_year = generated_container.generated_container_years[0]
        luy = generated_container_first_year.learning_unit_year_full
        requirement_entity = generated_container_first_year.requirement_entity_container_year
        central_manager = CentralManagerFactory(entity=requirement_entity)
        ProposalLearningUnitFactory(learning_unit_year=luy)
        self.assertTrue(central_manager.person.user.has_perm('base.can_edit_learning_unit_proposal', luy))

    @mock.patch('learning_unit.calendar.learning_unit_limited_proposal_management.'
                'LearningUnitLimitedProposalManagementCalendar.is_target_year_authorized',
                return_value=False)
    def test_access_edit_learning_unit_proposal_of_current_academic_year_as_faculty_manager(self, mock_period_closed):
        generated_container = GenerateContainer(start_year=self.academic_yr, end_year=self.academic_yr)
        generated_container_first_year = generated_container.generated_container_years[0]
        luy = generated_container_first_year.learning_unit_year_full
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year
        ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.MODIFICATION.name,
            state=proposal_state.ProposalState.FACULTY.name
        )
        faculty_manager = FacultyManagerFactory(entity=an_requirement_entity)
        self.assertFalse(faculty_manager.person.user.has_perm('base.can_edit_learning_unit_proposal', luy))

    def test_cannot_access_edit_learning_unit_central_proposal_state_as_faculty_manager(self):
        generated_container = GenerateContainer(start_year=self.academic_yr_1, end_year=self.academic_yr_1)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year

        luy = generated_container_first_year.learning_unit_year_full
        faculty_manager = FacultyManagerFactory(entity=an_requirement_entity)

        ProposalLearningUnitFactory(
            state=proposal_state.ProposalState.CENTRAL.name,
            type=proposal_type.ProposalType.MODIFICATION.name,
            learning_unit_year=luy
        )

        generate_proposal_calendars(
            [self.academic_yr, self.academic_yr_1, self.academic_yr_2, self.academic_yr_6]
        )

        self.assertFalse(faculty_manager.person.user.has_perm('base.can_edit_learning_unit_proposal', luy))

    def test_can_access_edit_learning_unit_modification_faculty_proposal_state_as_faculty_manager(self):
        generated_container = GenerateContainer(start_year=self.academic_yr_1, end_year=self.academic_yr_1)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year

        luy = generated_container_first_year.learning_unit_year_full
        faculty_manager = FacultyManagerFactory(entity=an_requirement_entity)

        ProposalLearningUnitFactory(
            state=proposal_state.ProposalState.FACULTY.name,
            type=proposal_type.ProposalType.MODIFICATION.name,
            learning_unit_year=luy
        )

        generate_proposal_calendars(
            [self.academic_yr, self.academic_yr_1, self.academic_yr_2, self.academic_yr_6]
        )

        self.assertTrue(faculty_manager.person.user.has_perm('base.can_edit_learning_unit_proposal', luy))

    def test_can_access_edit_learning_unit_creation_faculty_proposal_state_as_faculty_manager(self):
        generated_container = GenerateContainer(start_year=self.academic_yr_1, end_year=self.academic_yr_1)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year

        luy = generated_container_first_year.learning_unit_year_full
        faculty_manager = FacultyManagerFactory(entity=an_requirement_entity)

        ProposalLearningUnitFactory(
            state=proposal_state.ProposalState.FACULTY.name,
            type=proposal_type.ProposalType.CREATION.name,
            learning_unit_year=luy
        )

        generate_proposal_calendars(
            [self.academic_yr, self.academic_yr_1, self.academic_yr_2, self.academic_yr_6]
        )

        self.assertTrue(faculty_manager.person.user.has_perm('base.can_edit_learning_unit_proposal', luy))

    def test_is_not_eligible_for_cancel_of_proposal(self):
        luy = LearningUnitYearFactory(academic_year=self.academic_yr)
        an_entity = EntityFactory()
        luy.learning_container_year.requirement_entity = an_entity
        luy.initial_data = {"learning_container_year": SimpleNamespace(requirement_entity=an_entity.id)}
        luy.learning_container_year.save()
        a_person = CentralManagerFactory().person
        a_proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.SUPPRESSION.name,
            state=proposal_state.ProposalState.CENTRAL.name,
        )
        self.assertFalse(a_person.user.has_perm('base.can_cancel_proposal', luy))
        a_proposal.state = proposal_state.ProposalState.FACULTY.name
        a_proposal.save()
        self.assertFalse(a_person.user.has_perm('base.can_cancel_proposal', luy))
        a_proposal.type = proposal_type.ProposalType.MODIFICATION.name
        a_proposal.save()
        self.assertFalse(a_person.user.has_perm('base.can_cancel_proposal', luy))

    def test_is_eligible_for_cancel_of_proposal_for_creation(self):
        generated_container = GenerateContainer(start_year=self.academic_yr,
                                                end_year=self.academic_yr)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year

        luy = generated_container_first_year.learning_unit_year_full
        luy.initial_data = {"learning_container_year": {"requirement_entity": an_requirement_entity.id}}

        central_manager = CentralManagerFactory(entity=an_requirement_entity).person

        ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.CREATION.name,
            state=proposal_state.ProposalState.FACULTY.name
        )

        self.assertTrue(central_manager.user.has_perm('base.can_cancel_proposal', luy))

    def test_is_eligible_for_cancel_of_proposal(self):
        generated_container = GenerateContainer(start_year=self.academic_yr, end_year=self.academic_yr)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year

        luy = generated_container_first_year.learning_unit_year_full
        luy.initial_data = {"learning_container_year": {"requirement_entity": an_requirement_entity.id}}

        central_manager = CentralManagerFactory(entity=an_requirement_entity).person

        ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.MODIFICATION.name,
            state=proposal_state.ProposalState.FACULTY.name,
            initial_data={
                "learning_container_year": {
                    "requirement_entity": an_requirement_entity.id,
                }
            })

        self.assertTrue(central_manager.user.has_perm('base.can_cancel_proposal', luy))

    def test_is_eligible_for_cancel_of_proposal_wrong_state(self):
        generated_container = GenerateContainer(start_year=self.academic_yr,
                                                end_year=self.academic_yr)
        generated_container_first_year = generated_container.generated_container_years[0]
        an_requirement_entity = generated_container_first_year.requirement_entity_container_year

        luy = generated_container_first_year.learning_unit_year_full
        luy.initial_data = {"learning_container_year": {"requirement_entity": an_requirement_entity.id}}

        central_manager = CentralManagerFactory(entity=an_requirement_entity).person

        ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=proposal_type.ProposalType.MODIFICATION.name,
            state=proposal_state.ProposalState.CENTRAL.name,
            initial_data={
                "learning_container_year": {
                    "requirement_entity": an_requirement_entity.id,
                }
            })

        self.assertTrue(central_manager.user.has_perm('base.can_cancel_proposal', luy))

    def test_is_learning_unit_year_in_state_to_be_modified(self):
        luy = LearningUnitYearFactory(
            acronym="LDROI1004",
            specific_title="Juridic law courses",
            academic_year=self.academic_yr,
            subtype=learning_unit_year_subtypes.FULL,
            learning_container_year__requirement_entity=self.entity,
        )
        start_year = AcademicYearFactory(year=self.academic_yr.year - 3)
        end_year = AcademicYearFactory(year=self.academic_yr.year - 1)
        previous_academic_years = GenerateAcademicYear(start_year=start_year, end_year=end_year).academic_years
        next_academic_years = GenerateAcademicYear(
            start_year=self.academic_yr_1, end_year=self.academic_yr_6).academic_years
        previous_luys = [
            LearningUnitYearFactory(
                academic_year=ac,
                learning_unit=luy.learning_unit,
                learning_container_year__requirement_entity=self.entity
            ) for ac in previous_academic_years
        ]
        next_luys = [
            LearningUnitYearFactory(
                academic_year=ac,
                learning_unit=luy.learning_unit,
                learning_container_year__requirement_entity=self.entity
            ) for ac in next_academic_years
        ]

        learning_units_can_be_modified = [luy, next_luys[0], next_luys[1]]
        for luy in learning_units_can_be_modified:
            with self.subTest(luy=luy):
                self.assertTrue(self.faculty_manager.person.user.has_perm('base.can_edit_learningunit', luy))

        learning_units_cannot_be_modified = previous_luys + [next_luys[2], next_luys[3], next_luys[4]]
        for luy in learning_units_cannot_be_modified:
            with self.subTest(luy=luy):
                self.assertFalse(self.faculty_manager.person.user.has_perm('base.can_edit_learningunit', luy))

    def test_is_not_eligible_if_creation_proposal_has_application(self):
        central_manager = CentralManagerFactory()
        luy = LearningUnitYearFactory()
        luy.learning_container_year.requirement_entity = central_manager.entity
        luy.initial_data = {"learning_container_year": {"requirement_entity": central_manager.entity.id}}

        ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=ProposalType.CREATION.name
        )
        TutorApplicationFactory(learning_container_year=luy.learning_container_year)

        self.assertFalse(central_manager.person.user.has_perm('base.can_cancel_proposal', luy))


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
        academic_years = [cls.past_academic_year, cls.current_academic_year]
        generate_proposal_calendars_without_start_and_end_date(academic_years)

    def setUp(self):
        requirement_entity = EntityFactory()
        self.luy = LearningUnitYearFakerFactory(learning_container_year__academic_year=self.current_academic_year,
                                                learning_container_year__container_type=COURSE,
                                                subtype=FULL,
                                                learning_container_year__requirement_entity=requirement_entity)
        self.person = CentralManagerFactory(entity=requirement_entity).person

    def test_cannot_propose_modification_of_past_learning_unit(self):
        past_luy = LearningUnitYearFakerFactory(learning_container_year__academic_year=self.past_academic_year)

        self.assertFalse(self.person.user.has_perm('base.can_propose_learningunit', past_luy))

    def test_cannot_propose_modification_of_partim(self):
        self.luy.subtype = PARTIM
        self.luy.save()

        self.assertFalse(self.person.user.has_perm('base.can_propose_learningunit', self.luy))

    def test_can_only_propose_modification_for_course_internship_and_dissertation(self):
        other_types = (OTHER_COLLECTIVE, OTHER_INDIVIDUAL, MASTER_THESIS, EXTERNAL)
        for luy_container_type in other_types:
            with self.subTest(luy_container_type=luy_container_type):
                self.luy.learning_container_year.container_type = luy_container_type
                self.luy.learning_container_year.save()
                self.assertFalse(self.person.user.has_perm('base.can_propose_learningunit', self.luy))

    def test_can_only_propose_modification_for_luy_which_is_not_currently_in_proposition(self):
        ProposalLearningUnitFactory(learning_unit_year=self.luy)

        self.assertFalse(self.person.user.has_perm('base.can_propose_learningunit', self.luy))

    def test_can_only_propose_modification_for_lu_which_is_not_in_proposition_on_different_year(self):
        past_luy_with_proposal = LearningUnitYearFakerFactory(
            learning_container_year__academic_year=self.past_academic_year,
            learning_unit=self.luy.learning_unit
        )
        ProposalLearningUnitFactory(learning_unit_year=past_luy_with_proposal)

        self.assertFalse(self.person.user.has_perm('base.can_propose_learningunit', self.luy))

    def test_cannot_propose_modification_for_luy_for_which_person_is_not_linked_to_entity(self):
        person = CentralManagerFactory().person
        self.assertFalse(person.user.has_perm('base.can_propose_learningunit', self.luy))

    def test_all_requirements_are_met_to_propose_modification(self):
        for luy_container_type in [type.name for type in FACULTY_EDITABLE_CONTAINER_TYPES]:
            with self.subTest(luy_container_type=luy_container_type):
                self.luy.learning_container_year.container_type = luy_container_type
                self.luy.learning_container_year.save()
                self.assertTrue(self.person.user.has_perm('base.can_propose_learningunit', self.luy))

    def test_check_proposal_edition_ok(self):
        past_luy_with_proposal = LearningUnitYearFakerFactory(
            academic_year=self.past_academic_year,
            learning_container_year__academic_year=self.past_academic_year,
            learning_container_year__requirement_entity=self.luy.learning_container_year.requirement_entity,
            learning_unit=self.luy.learning_unit
        )
        past_luy_with_proposal.initial_data = {
            'learning_container_year': self.luy.learning_container_year
        }
        ProposalLearningUnitFactory(learning_unit_year=past_luy_with_proposal)

        self.assertTrue(self.person.user.has_perm('base.can_edit_learning_unit_proposal', past_luy_with_proposal))

    def test_check_proposal_edition_ko(self):
        past_luy = LearningUnitYearFakerFactory(
            academic_year=self.past_academic_year,
            learning_container_year__academic_year=self.past_academic_year,
            learning_container_year__requirement_entity=self.luy.learning_container_year.requirement_entity,
            learning_unit=self.luy.learning_unit
        )
        past_luy.initial_data = {
            'learning_container_year': self.luy.learning_container_year
        }

        self.assertFalse(self.person.user.has_perm('base.can_edit_learning_unit_proposal', past_luy))


class TestIsEligibleToConsolidateLearningUnitProposal(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.central_manager = CentralManagerFactory()
        cls.person = PersonFactory()

    def test_when_person_has_no_right_to_consolidate(self):
        luy = ProposalLearningUnitFactory(state=proposal_state.ProposalState.ACCEPTED.name).learning_unit_year
        self.assertFalse(self.person.user.has_perm('base.can_consolidate_learningunit_proposal', luy))

    def test_when_person_has_right_to_consolidate_but_proposal_state_is_neither_accepted_nor_refused(self):
        states = (
            state.name for state in proposal_state.ProposalState if state not in (
                proposal_state.ProposalState.ACCEPTED, proposal_state.ProposalState.REFUSED
            )
        )
        for state in states:
            with self.subTest(state=state):
                luy = ProposalLearningUnitFactory(state=state).learning_unit_year
                user = self.central_manager.person.user
                self.assertFalse(user.has_perm('base.can_consolidate_learningunit_proposal', luy))

    def test_when_person_not_linked_to_entity(self):
        proposal = ProposalLearningUnitFactory(
            state=proposal_state.ProposalState.ACCEPTED.name,
            learning_unit_year__learning_container_year__requirement_entity=EntityFactory(),
        )
        proposal.learning_unit_year.initial_data = {
            'learning_container_year': proposal.learning_unit_year.learning_container_year
        }
        user = self.central_manager.person.user
        self.assertFalse(user.has_perm('base.can_consolidate_learningunit_proposal', proposal.learning_unit_year))

    def test_when_person_is_linked_to_entity(self):
        states = (
            state.name for state in proposal_state.ProposalState
            if state in (proposal_state.ProposalState.ACCEPTED, proposal_state.ProposalState.REFUSED)
        )

        for state in states:
            with self.subTest(state=state):
                proposal = ProposalLearningUnitFactory(state=state)
                container_year = proposal.learning_unit_year.learning_container_year
                container_year.requirement_entity = EntityFactory()
                container_year.save()

                user = CentralManagerFactory(entity=container_year.requirement_entity).person.user
                generate_learning_unit_edition_calendars([container_year.academic_year])
                self.assertTrue(
                    user.has_perm('base.can_consolidate_learningunit_proposal', proposal.learning_unit_year)
                )

    def test_is_not_eligible_consolidate_delete_proposal_if_has_applications(self):
        requirement_entity = EntityFactory()
        luy = LearningUnitYearFactory(learning_container_year__requirement_entity=requirement_entity)
        proposal = ProposalLearningUnitFactory(
            learning_unit_year=luy,
            type=ProposalType.SUPPRESSION.name,
            state=ProposalState.ACCEPTED.name
        )
        TutorApplicationFactory(learning_container_year=luy.learning_container_year)
        user = CentralManagerFactory(entity=requirement_entity).person.user
        self.assertFalse(user.has_perm('base.can_consolidate_learningunit_proposal', proposal.learning_unit_year))


class TestIsAcademicYearInRangeToCreatePartim(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_acy = create_current_academic_year()
        start_year = AcademicYearFactory(year=cls.current_acy.year - LEARNING_UNIT_CREATION_SPAN_YEARS)
        end_year = AcademicYearFactory(year=cls.current_acy.year + LEARNING_UNIT_CREATION_SPAN_YEARS)
        cls.generated_ac_years = GenerateAcademicYear(start_year, end_year)
        cls.academic_years = GenerateAcademicYear(start_year, end_year).academic_years
        cls.academic_years[LEARNING_UNIT_CREATION_SPAN_YEARS] = cls.current_acy
        entity = EntityVersionFactory().entity
        cls.learning_unit_years = [
            LearningUnitYearFactory(
                academic_year=acy,
                learning_container_year__requirement_entity=entity,
                subtype=learning_unit_year_subtypes.FULL
            )
            for acy in cls.academic_years
        ]
        generate_learning_unit_edition_calendars(cls.academic_years)

        cls.central_manager = CentralManagerFactory(entity=entity)
        cls.faculty_manager_for_ue = FacultyManagerFactory(entity=entity)

    def test_for_faculty_manager_for_ue(self):
        person = self.faculty_manager_for_ue.person
        for luy in self.learning_unit_years:
            with self.subTest(academic_year=luy.academic_year):
                if luy.academic_year.year <= self.current_acy.year + MAX_ACADEMIC_YEAR_FACULTY:
                    self.assertTrue(person.user.has_perm('base.can_create_partim', luy))
                else:
                    self.assertFalse(person.user.has_perm('base.can_create_partim', luy))

    def test_for_central_manager(self):
        person = self.central_manager.person
        for luy in self.learning_unit_years:
            with self.subTest(academic_year=luy.academic_year):
                self.assertTrue(person.user.has_perm('base.can_create_partim', luy))


class PermsViewAcademicActorCase(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_has_no_perms(self):
        self.assertFalse(view_academicactors(self.user))

    def test_has_valid_perms(self):
        self.user.user_permissions.add(Permission.objects.get(codename="view_programmanager"))
        self.user.refresh_from_db()
        self.assertTrue(view_academicactors(self.user))
