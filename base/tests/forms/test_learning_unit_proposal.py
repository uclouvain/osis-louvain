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
from decimal import Decimal

from django.contrib.auth.models import Group
from django.test import TestCase

from base.forms.learning_unit import learning_unit_create_2
from base.forms.learning_unit_proposal import ProposalBaseForm
from base.forms.proposal import learning_unit_proposal
from base.models import proposal_learning_unit, academic_year as academic_year_mdl
from base.models.enums import organization_type, proposal_type, proposal_state, entity_type, \
    learning_container_year_types, quadrimesters, entity_container_year_link_type, \
    learning_unit_year_periodicity, internship_subtypes, learning_unit_year_subtypes
from base.models.enums.entity_type import SCHOOL
from base.models.enums.groups import CENTRAL_MANAGER_GROUP, FACULTY_MANAGER_GROUP
from base.models.enums.proposal_state import ProposalState
from base.models.enums.proposal_type import ProposalType
from base.models.learning_unit_year import LearningUnitYear
from base.tests.factories.academic_calendar import generate_creation_or_end_date_proposal_calendars
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateAcademicYear
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group import FacultyManagerGroupFactory, CentralManagerGroupFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory, FacultyManagerFactory, CentralManagerFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from reference.tests.factories.language import LanguageFactory

PROPOSAL_TYPE = proposal_type.ProposalType.TRANSFORMATION_AND_MODIFICATION.name
PROPOSAL_STATE = proposal_state.ProposalState.FACULTY.name


class TestSave(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.an_organization = OrganizationFactory(type=organization_type.MAIN)
        cls.current_academic_year = create_current_academic_year()
        cls.academic_years = GenerateAcademicYear(
            AcademicYearFactory(year=cls.current_academic_year.year - 10),
            AcademicYearFactory(year=cls.current_academic_year.year + 10)
        )
        generate_creation_or_end_date_proposal_calendars(cls.academic_years)
        today = datetime.date.today()
        cls.an_entity = EntityFactory(organization=cls.an_organization)
        cls.entity_version = EntityVersionFactory(entity=cls.an_entity, entity_type=entity_type.FACULTY,
                                                  start_date=today.replace(year=1900),
                                                  end_date=None)
        cls.an_entity_school = EntityFactory(organization=cls.an_organization)
        cls.entity_version_school = EntityVersionFactory(entity=cls.an_entity_school, entity_type=entity_type.SCHOOL,
                                                         start_date=today.replace(year=1900),
                                                         end_date=None)
        cls.learning_container_year = LearningContainerYearFactory(
            academic_year=cls.current_academic_year,
            container_type=learning_container_year_types.COURSE,
            requirement_entity=cls.entity_version.entity,
        )
        cls.language = LanguageFactory(code="EN")
        cls.campus = CampusFactory(name="OSIS Campus", organization=OrganizationFactory(type=organization_type.MAIN),
                                   is_administration=True)
        FacultyManagerGroupFactory()
        CentralManagerGroupFactory()
        cls.learning_unit_year = LearningUnitYearFakerFactory(
            credits=Decimal(5),
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=cls.current_academic_year,
            learning_container_year=cls.learning_container_year,
            campus=CampusFactory(organization=cls.an_organization, is_administration=True),
            periodicity=learning_unit_year_periodicity.ANNUAL,
            internship_subtype=None
        )
        cls.form_data = {
            "academic_year": cls.learning_unit_year.academic_year.id,
            "acronym_0": "L",
            "acronym_1": "OSIS1245",
            "common_title": "New common title",
            "common_title_english": "New common title english",
            "specific_title": "New title",
            "specific_title_english": "New title english",
            "container_type": cls.learning_unit_year.learning_container_year.container_type,
            "internship_subtype": "",
            "credits": cls.learning_unit_year.credits,
            "periodicity": learning_unit_year_periodicity.BIENNIAL_ODD,
            "status": False,
            "language": cls.language.pk,
            "quadrimester": quadrimesters.Q1,
            "campus": cls.campus.id,
            "entity": cls.entity_version.id,
            "folder_id": "1",
            "state": proposal_state.ProposalState.CENTRAL.name,
            'requirement_entity': cls.entity_version.id,
            'allocation_entity': cls.entity_version.id,
            'additional_entity_1': cls.entity_version.id,
            'additional_entity_2': cls.entity_version.id,

            # Learning component year data model form
            'component-TOTAL_FORMS': '2',
            'component-INITIAL_FORMS': '0',
            'component-MAX_NUM_FORMS': '2',
            'component-0-hourly_volume_total_annual': Decimal(20),
            'component-0-hourly_volume_partial_q1': Decimal(10),
            'component-0-hourly_volume_partial_q2': Decimal(10),
            'component-1-hourly_volume_total_annual': Decimal(20),
            'component-1-hourly_volume_partial_q1': Decimal(10),
            'component-1-hourly_volume_partial_q2': Decimal(10),
            'component-0-planned_classes': 1,
            'component-1-planned_classes': 1,
        }

    def setUp(self):
        self.person = PersonFactory()
        self.person_entity = PersonEntityFactory(person=self.person, entity=self.an_entity)

    def test_learning_unit_proposal_form_get_as_faculty_manager(self):
        self.person.user.groups.add(Group.objects.get(name=FACULTY_MANAGER_GROUP))
        form = ProposalBaseForm(self.form_data, self.person, self.learning_unit_year)
        self.assertTrue(form.fields['state'].disabled)

    def test_learning_unit_proposal_form_get_as_central_manager(self):
        self.person.user.groups.add(Group.objects.get(name=CENTRAL_MANAGER_GROUP))
        form = ProposalBaseForm(self.form_data, self.person, self.learning_unit_year)
        self.assertFalse(form.fields['state'].disabled)

    def test_learning_unit_proposal_form_get_as_central_manager_with_instance(self):
        self.person.user.groups.add(Group.objects.get(name=CENTRAL_MANAGER_GROUP))
        proposal = ProposalLearningUnitFactory(
            learning_unit_year=self.learning_unit_year, state=ProposalState.FACULTY.name,
            entity=self.entity_version.entity)
        form = ProposalBaseForm(self.form_data, self.person, self.learning_unit_year, proposal=proposal)
        self.assertFalse(form.fields['state'].disabled)
        self.assertEqual(form.fields['state'].initial, ProposalState.FACULTY.name)

    def test_learning_unit_year_update(self):
        form = ProposalBaseForm(self.form_data, self.person, self.learning_unit_year)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        learning_unit_year = LearningUnitYear.objects.get(pk=self.learning_unit_year.id)
        self._assert_acronym_has_changed_in_proposal(learning_unit_year)
        self._assert_common_titles_stored_in_container(learning_unit_year)
        self.assertFalse(learning_unit_year.status)
        self.assertEqual(learning_unit_year.credits, Decimal(self.form_data['credits']))
        self.assertEqual(learning_unit_year.quadrimester, self.form_data['quadrimester'])
        self.assertEqual(learning_unit_year.specific_title, self.form_data["specific_title"])
        self.assertEqual(learning_unit_year.specific_title_english, self.form_data["specific_title_english"])
        self.assertEqual(learning_unit_year.language, self.language)
        self.assertEqual(learning_unit_year.campus, self.campus)

    def _assert_acronym_has_changed_in_proposal(self, learning_unit_year):
        self.assertEqual(learning_unit_year.acronym,
                         "{}{}".format(self.form_data['acronym_0'], self.form_data['acronym_1']))

    def _assert_common_titles_stored_in_container(self, learning_unit_year):
        self.assertNotEqual(learning_unit_year.specific_title, self.form_data['common_title'])
        self.assertNotEqual(learning_unit_year.specific_title_english, self.form_data['common_title_english'])
        self.assertEqual(learning_unit_year.learning_container_year.common_title, self.form_data['common_title'])
        self.assertEqual(learning_unit_year.learning_container_year.common_title_english,
                         self.form_data['common_title_english'])

    def test_learning_container_update(self):
        form = ProposalBaseForm(self.form_data, self.person, self.learning_unit_year)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        learning_unit_year = LearningUnitYear.objects.get(pk=self.learning_unit_year.id)
        learning_container_year = learning_unit_year.learning_container_year

        self.assertEqual(learning_unit_year.acronym, self.form_data['acronym_0'] + self.form_data['acronym_1'])
        self.assertEqual(learning_container_year.common_title, self.form_data['common_title'])
        self.assertEqual(learning_container_year.common_title_english, self.form_data['common_title_english'])

    def test_requirement_entity(self):
        form = ProposalBaseForm(self.form_data, self.person, self.learning_unit_year)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        container = self.learning_unit_year.learning_container_year
        container.refresh_from_db()
        self.assertEqual(container.requirement_entity, self.entity_version.entity)

    def test_with_all_entities_set(self):
        today = datetime.date.today()
        entity_1 = EntityFactory(organization=OrganizationFactory(type=organization_type.MAIN))
        additional_entity_version_1 = EntityVersionFactory(entity_type=entity_type.SCHOOL,
                                                           start_date=today.replace(year=1900),
                                                           end_date=today.replace(year=today.year + 1),
                                                           entity=entity_1)
        entity_2 = EntityFactory(organization=OrganizationFactory(type=organization_type.MAIN))
        additional_entity_version_2 = EntityVersionFactory(entity_type=entity_type.SCHOOL,
                                                           start_date=today.replace(year=1900),
                                                           end_date=today.replace(year=today.year + 1),
                                                           entity=entity_2)
        self.form_data["allocation_entity"] = self.entity_version.id
        self.form_data["additional_entity_1"] = additional_entity_version_1.id
        self.form_data["additional_entity_2"] = additional_entity_version_2.id

        form = ProposalBaseForm(self.form_data, self.person, self.learning_unit_year)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.learning_unit_year.learning_container_year.refresh_from_db()
        entities_by_type = self.learning_unit_year.learning_container_year.get_map_entity_by_type()

        expected_entities = {
            entity_container_year_link_type.REQUIREMENT_ENTITY: self.entity_version.entity,
            entity_container_year_link_type.ALLOCATION_ENTITY: self.entity_version.entity,
            entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1: additional_entity_version_1.entity,
            entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2: additional_entity_version_2.entity
        }
        self.assertDictEqual(entities_by_type, expected_entities)

    def test_modify_learning_container_subtype(self):
        self.learning_unit_year.learning_container_year.container_type = learning_container_year_types.INTERNSHIP
        self.learning_unit_year.internship_subtype = internship_subtypes.CLINICAL_INTERNSHIP
        self.learning_unit_year.learning_container_year.save()
        self.learning_unit_year.save()
        self.form_data["container_type"] = learning_container_year_types.INTERNSHIP
        self.form_data["internship_subtype"] = internship_subtypes.TEACHING_INTERNSHIP

        form = ProposalBaseForm(self.form_data, self.person, self.learning_unit_year)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.learning_unit_year.refresh_from_db()

        self.assertEqual(self.learning_unit_year.learning_container_year.container_type,
                         learning_container_year_types.INTERNSHIP)
        self.assertEqual(self.learning_unit_year.internship_subtype, internship_subtypes.TEACHING_INTERNSHIP)

    def test_creation_proposal_learning_unit(self):
        self.maxDiff = None
        form = ProposalBaseForm(self.form_data, self.person, self.learning_unit_year)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        a_proposal_learning_unt = proposal_learning_unit.find_by_learning_unit_year(self.learning_unit_year)

        self.assertEqual(a_proposal_learning_unt.type, PROPOSAL_TYPE)
        self.assertEqual(a_proposal_learning_unt.state, PROPOSAL_STATE)
        self.assertEqual(a_proposal_learning_unt.author, self.person)
        self.assertDictEqual(a_proposal_learning_unt.initial_data, self._get_initial_data_expected())

    def _get_initial_data_expected(self):
        initial_data_expected = build_initial_data(self.learning_unit_year, self.entity_version.entity)
        initial_data_expected["learning_unit_year"]["credits"] = '5.00'
        initial_data_expected['entities'] = {
            entity_container_year_link_type.REQUIREMENT_ENTITY: self.entity_version.entity.id,
            entity_container_year_link_type.ALLOCATION_ENTITY: None,
            entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1: None,
            entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2: None
        }
        return initial_data_expected

    def test_when_setting_additional_entity_to_none(self):
        self.form_data['additional_entity_1'] = None
        form = ProposalBaseForm(self.form_data, self.person, self.learning_unit_year)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

        self.learning_unit_year.learning_container_year.refresh_from_db()
        self.assertIsNone(self.learning_unit_year.learning_container_year.additional_entity_1)

    def test_creation_proposal_learning_unit_with_school_entity(self):
        self.entity_version.entity_type = SCHOOL
        self.entity_version.save()
        form = ProposalBaseForm(self.form_data, self.person, self.learning_unit_year)
        self.assertTrue('entity' in form.errors[0])

    def test_creation_proposal_learning_unit_with_not_linked_entity(self):
        self.person_entity.entity = self.an_entity_school
        self.person_entity.save()
        form = ProposalBaseForm(self.form_data, self.person, self.learning_unit_year)
        self.assertTrue('entity' in form.errors[1])

    def test_academic_year_range_creation_proposal_central_manager(self):
        LanguageFactory(code="FR")
        central_manager = CentralManagerFactory()
        form = learning_unit_create_2.FullForm(
            central_manager,
            self.learning_unit_year.academic_year,
            start_year=self.learning_unit_year.academic_year,
            proposal_type=ProposalType.CREATION.name
        )
        self.assertCountEqual(
            list(form.fields['academic_year'].queryset),
            list(academic_year_mdl.find_academic_years(
                start_year=self.current_academic_year.year,
                end_year=self.current_academic_year.year + 6
            ))
        )

    def test_academic_year_range_creation_proposal_faculty_manager(self):
        LanguageFactory(code="FR")
        faculty_manager = FacultyManagerFactory()
        form = learning_unit_create_2.FullForm(
            faculty_manager,
            self.learning_unit_year.academic_year,
            start_year=self.learning_unit_year.academic_year,
            proposal_type=ProposalType.CREATION.name
        )
        self.assertCountEqual(
            list(form.fields['academic_year'].queryset),
            list(academic_year_mdl.find_academic_years(
                start_year=self.current_academic_year.year + 1,
                end_year=self.current_academic_year.year + 6
            ))
        )


def build_initial_data(learning_unit_year, entity):
    initial_data_expected = {
        "learning_container_year": {
            "id": learning_unit_year.learning_container_year.id,
            "acronym": learning_unit_year.acronym,
            "common_title": learning_unit_year.learning_container_year.common_title,
            "container_type": learning_unit_year.learning_container_year.container_type,
            "in_charge": learning_unit_year.learning_container_year.in_charge,
            "team": learning_unit_year.learning_container_year.team,
            "common_title_english": learning_unit_year.learning_container_year.common_title_english,
            "is_vacant": learning_unit_year.learning_container_year.is_vacant,
            "type_declaration_vacant": learning_unit_year.learning_container_year.type_declaration_vacant,
            "requirement_entity": entity.id,
            "allocation_entity": None,
            "additional_entity_1": None,
            "additional_entity_2": None,
        },
        "learning_unit_year": {
            "id": learning_unit_year.id,
            "acronym": learning_unit_year.acronym,
            "specific_title": learning_unit_year.specific_title,
            "internship_subtype": learning_unit_year.internship_subtype,
            "language": learning_unit_year.language.pk,
            "credits": '5',
            "campus": learning_unit_year.campus.id,
            "periodicity": learning_unit_year.periodicity,
            "status": learning_unit_year.status,
            "session": learning_unit_year.session,
            "quadrimester": learning_unit_year.quadrimester,
            "specific_title_english": learning_unit_year.specific_title_english,
            "professional_integration": learning_unit_year.professional_integration,
            "attribution_procedure": learning_unit_year.attribution_procedure,
        },
        "learning_unit": {
            "id": learning_unit_year.learning_unit.id,
            'end_year': learning_unit_year.learning_unit.end_year,
            "other_remark": learning_unit_year.learning_unit.other_remark,
            "faculty_remark": learning_unit_year.learning_unit.faculty_remark,
        },
        "learning_component_years": [],
        "volumes": {}
    }
    return initial_data_expected


class TestProposalLearningUnitFilter(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_years = AcademicYearFactory.produce(None, 2, 5)
        generate_creation_or_end_date_proposal_calendars(cls.academic_years)

    def test_initial_value_with_entity_subordinated(self):
        proposal_filter = learning_unit_proposal.ProposalLearningUnitFilter()
        self.assertTrue(proposal_filter.form.fields['with_entity_subordinated'].initial)
        self.assertEqual(
            proposal_filter.form.fields['academic_year'].initial,
            self.academic_years[3]  # Index 3 is n+1 because we produced academic years from n-2 in setUpTestData
        )
