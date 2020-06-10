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

from django.contrib import messages
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponseNotFound, HttpResponse, HttpResponseForbidden
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from waffle.testutils import override_flag

from attribution.tests.factories.attribution_charge_new import AttributionChargeNewFactory
from attribution.tests.factories.attribution_new import AttributionNewFactory
from base.business import learning_unit_proposal as proposal_business
from base.business.learning_unit_proposal import INITIAL_DATA_FIELDS, copy_learning_unit_data
from base.forms.learning_unit.edition import LearningUnitProposalEndDateForm
from base.forms.learning_unit_proposal import ProposalLearningUnitForm
from base.models import proposal_learning_unit
from base.models.academic_year import AcademicYear
from base.models.enums import groups
from base.models.enums import learning_component_year_type
from base.models.enums import learning_unit_year_periodicity
from base.models.enums import organization_type, entity_type, \
    learning_unit_year_subtypes, proposal_type, learning_container_year_types, proposal_state
from base.models.enums.proposal_state import ProposalState, LimitedProposalState
from base.models.enums.proposal_type import ProposalType
from base.tests.factories import campus as campus_factory, organization as organization_factory, \
    person as person_factory
from base.tests.factories.academic_calendar import generate_modification_transformation_proposal_calendars, \
    generate_creation_or_end_date_proposal_calendars
from base.tests.factories.academic_year import create_current_academic_year, \
    AcademicYearFactory
from base.tests.factories.business.learning_units import GenerateContainer
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity import EntityFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.group import CentralManagerGroupFactory, FacultyManagerGroupFactory
from base.tests.factories.learning_component_year import LearningComponentYearFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit import LearningUnitFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFakerFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.tutor import TutorFactory
from base.tests.factories.user import UserFactory
from base.views.learning_units.proposal.update import update_learning_unit_proposal, \
    learning_unit_modification_proposal, learning_unit_suppression_proposal
from base.views.learning_units.search.proposal import ACTION_CONSOLIDATE, ACTION_BACK_TO_INITIAL, ACTION_FORCE_STATE
from reference.tests.factories.language import LanguageFactory, FrenchLanguageFactory

LABEL_VALUE_BEFORE_PROPOSAL = _('Value before proposal')


@override_flag('learning_unit_proposal_update', active=True)
class TestLearningUnitModificationProposal(TestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearFactory.produce(number_past=3, number_future=10)
        cls.person = person_factory.PersonWithPermissionsFactory("can_propose_learningunit", "can_access_learningunit")

        an_organization = OrganizationFactory(type=organization_type.MAIN)
        current_academic_year = create_current_academic_year()
        cls.entity_version = EntityVersionFactory(
            entity__organization=an_organization,
            entity_type=entity_type.FACULTY,
            start_date=current_academic_year.start_date,
            end_date=current_academic_year.end_date
        )
        learning_container_year = LearningContainerYearFactory(
            acronym="LOSIS1212",
            academic_year=current_academic_year,
            container_type=learning_container_year_types.COURSE,
            requirement_entity=cls.entity_version.entity,
            allocation_entity=cls.entity_version.entity,
            additional_entity_1=cls.entity_version.entity,
            additional_entity_2=cls.entity_version.entity,
        )
        cls.learning_unit_year = LearningUnitYearFakerFactory(
            acronym=learning_container_year.acronym,
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=current_academic_year,
            learning_container_year=learning_container_year,
            quadrimester=None,
            specific_title_english="title english",
            campus=CampusFactory(organization=an_organization, is_administration=True),
            internship_subtype=None
        )

        cls.person_entity = PersonEntityFactory(
            person=cls.person,
            entity=cls.entity_version.entity,
            with_child=True
        )

        cls.url = reverse(learning_unit_modification_proposal, args=[cls.learning_unit_year.id])

        cls.form_data = {
            "academic_year": cls.learning_unit_year.academic_year.id,
            "acronym_0": cls.learning_unit_year.acronym[0],
            "acronym_1": cls.learning_unit_year.acronym[1:],
            "common_title": cls.learning_unit_year.learning_container_year.common_title,
            "common_title_english": cls.learning_unit_year.learning_container_year.common_title_english,
            "specific_title": cls.learning_unit_year.specific_title,
            "specific_title_english": cls.learning_unit_year.specific_title_english,
            "container_type": cls.learning_unit_year.learning_container_year.container_type,
            "internship_subtype": "",
            "credits": cls.learning_unit_year.credits,
            "periodicity": cls.learning_unit_year.periodicity,
            "status": cls.learning_unit_year.status,
            "language": cls.learning_unit_year.language.pk,
            "quadrimester": "",
            "campus": cls.learning_unit_year.campus.id,
            "session": cls.learning_unit_year.session,
            "entity": cls.entity_version.id,
            "folder_id": "1",
            "state": proposal_state.ProposalState.FACULTY.name,
            'requirement_entity': cls.entity_version.id,
            'allocation_entity': cls.entity_version.id,
            'additional_entity_1': cls.entity_version.id,
            'additionanl_entity_2': cls.entity_version.id,

            # Learning component year data model form
            'component-TOTAL_FORMS': '2',
            'component-INITIAL_FORMS': '0',
            'component-MAX_NUM_FORMS': '2',
            'component-0-hourly_volume_total_annual': 20,
            'component-0-hourly_volume_partial_q1': 10,
            'component-0-hourly_volume_partial_q2': 10,
            'component-0-planned_classes': 1,
            'component-1-hourly_volume_total_annual': 20,
            'component-1-hourly_volume_partial_q1': 10,
            'component-1-hourly_volume_partial_q2': 10,
            'component-1-planned_classes': 1,
        }
        cls.academic_year_for_suppression_proposal = AcademicYear.objects.filter(
            year=cls.learning_unit_year.academic_year.year - 1)

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_user_has_not_permission(self):
        person = person_factory.PersonFactory()
        self.client.force_login(person.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_get_request(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'learning_unit/proposal/create_modification.html')
        self.assertEqual(response.context['learning_unit_year'], self.learning_unit_year)
        self.assertEqual(response.context['person'], self.person)
        self.assertIsInstance(response.context['form_proposal'], ProposalLearningUnitForm)

        luy_initial = response.context['learning_unit_year_form'].initial
        lcy_initial = response.context['learning_container_year_form'].initial
        self.assertEqual(luy_initial['academic_year'], self.learning_unit_year.academic_year.id)
        self.assertEqual(luy_initial['acronym'], [
            self.learning_unit_year.acronym[0], self.learning_unit_year.acronym[1:]])
        self.assertEqual(luy_initial['specific_title'], self.learning_unit_year.specific_title)
        self.assertEqual(lcy_initial['container_type'], self.learning_unit_year.
                         learning_container_year.container_type)
        self.assertEqual(luy_initial['credits'], self.learning_unit_year.credits)
        self.assertEqual(luy_initial['periodicity'], self.learning_unit_year.periodicity)
        self.assertEqual(luy_initial['status'], self.learning_unit_year.status)
        self.assertEqual(luy_initial['language'], self.learning_unit_year.language.pk)
        self.assertEqual(luy_initial['campus'], self.learning_unit_year.campus.id)

    def test_post_request_with_invalid_form(self):
        response = self.client.post(self.url, data={})

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'learning_unit/proposal/create_modification.html')
        self.assertEqual(response.context['learning_unit_year'], self.learning_unit_year)
        self.assertEqual(response.context['person'], self.person)
        self.assertIsInstance(response.context['form_proposal'], ProposalLearningUnitForm)

    def test_post_request(self):
        response = self.client.post(self.url, data=self.form_data)

        redirected_url = reverse("learning_unit", args=[self.learning_unit_year.id])
        self.assertRedirects(response, redirected_url, fetch_redirect_response=False)

        a_proposal_learning_unit = proposal_learning_unit.find_by_learning_unit_year(self.learning_unit_year)
        self.assertTrue(a_proposal_learning_unit)
        self.assertEqual(a_proposal_learning_unit.author, self.person)

        messages_list = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertIn(
            _("You proposed a modification of type %(type)s for the learning unit %(acronym)s.") % {
                'type': proposal_type.ProposalType.MODIFICATION.value,
                'acronym': self.learning_unit_year.acronym
            },
            list(messages_list))

    def test_initial_data_fields(self):
        expected_initial_data_fields = {
            'learning_container_year': [
                "id", "acronym", "common_title", "container_type", "in_charge", "common_title_english", "team",
                "is_vacant", "type_declaration_vacant",
                'requirement_entity', 'allocation_entity', 'additional_entity_1', 'additional_entity_2',
            ],
            'learning_unit': [
                "id", "end_year", "faculty_remark", "other_remark",
            ],
            'learning_unit_year': [
                "id", "acronym", "specific_title", "internship_subtype", "credits", "campus", "language", "periodicity",
                "status", "professional_integration", "specific_title", "specific_title_english", "quadrimester",
                "session", "attribution_procedure",
            ],
            'learning_component_year': [
                "id", "acronym", "hourly_volume_total_annual", "hourly_volume_partial_q1", "hourly_volume_partial_q2",
                "planned_classes", "type", "repartition_volume_requirement_entity",
                "repartition_volume_additional_entity_1", "repartition_volume_additional_entity_2"
            ],
        }

        self.assertEqual(expected_initial_data_fields, INITIAL_DATA_FIELDS)

    def test_proposal_already_exists(self):
        ProposalLearningUnitFactory(learning_unit_year=self.learning_unit_year)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")


@override_flag('learning_unit_proposal_update', active=True)
class TestLearningUnitSuppressionProposal(TestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearFactory.produce(number_past=3, number_future=10)
        cls.person = person_factory.CentralManagerForUEFactory("can_propose_learningunit", "can_access_learningunit")
        an_organization = OrganizationFactory(type=organization_type.MAIN)
        cls.academic_years = AcademicYearFactory.produce_in_future(quantity=8)
        cls.current_academic_year = cls.academic_years[0]
        cls.next_academic_year = cls.academic_years[1]
        generate_creation_or_end_date_proposal_calendars(cls.academic_years)

        cls.entity_version = EntityVersionFactory(
            entity__organization=an_organization,
            entity_type=entity_type.FACULTY,
            start_date=cls.current_academic_year.start_date,
            end_date=cls.academic_years[7].end_date
        )
        learning_container_year = LearningContainerYearFactory(
            academic_year=cls.current_academic_year,
            container_type=learning_container_year_types.COURSE,
            requirement_entity=cls.entity_version.entity,
            allocation_entity=cls.entity_version.entity,
        )
        cls.learning_unit = LearningUnitFactory(
            start_year=AcademicYear.objects.first(),
            end_year=None
        )

        cls.learning_unit_year = LearningUnitYearFakerFactory(
            acronym="LOSIS1212",
            subtype=learning_unit_year_subtypes.FULL,
            academic_year=cls.current_academic_year,
            learning_container_year=learning_container_year,
            quadrimester=None,
            learning_unit=cls.learning_unit,
            campus=CampusFactory(
                organization=an_organization,
                is_administration=True
            ),
            periodicity=learning_unit_year_periodicity.ANNUAL
        )

        cls.person_entity = PersonEntityFactory(
            person=cls.person,
            entity=cls.entity_version.entity,
            with_child=True
        )

        cls.url = reverse(learning_unit_suppression_proposal, args=[cls.learning_unit_year.id])

        cls.academic_year_for_suppression_proposal = AcademicYear.objects.filter(
            year=cls.learning_unit_year.academic_year.year - 1)

        cls.form_data = {
            "academic_year": cls.academic_year_for_suppression_proposal.first().id,
            "entity": cls.entity_version.id,
            "folder_id": "1",
            "state": ProposalState.FACULTY.name
        }

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_get_request(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, 'learning_unit/proposal/create_suppression.html')
        self.assertEqual(response.context['learning_unit_year'], self.learning_unit_year)
        self.assertEqual(response.context['person'], self.person)

        self.assertIsInstance(response.context['form_proposal'], ProposalLearningUnitForm)
        self.assertIsInstance(response.context['form_end_date'], LearningUnitProposalEndDateForm)
        self.assertCountEqual(
            list(response.context['form_end_date'].fields['academic_year'].queryset),
            list(self.academic_year_for_suppression_proposal)
        )

        form_proposal = response.context['form_proposal']
        form_end_date = response.context['form_end_date']

        self.assertEqual(form_end_date.fields['academic_year'].initial, None)
        self.assertTrue(form_end_date.fields['academic_year'].required)
        self.assertEqual(form_proposal.fields['folder_id'].initial, None)
        self.assertEqual(form_proposal.fields['entity'].initial, None)

    def test_get_request_academic_year_list_in_form_for_central_manager(self):
        person_factory.add_person_to_groups(self.person, [groups.CENTRAL_MANAGER_GROUP])
        response = self.client.get(self.url)
        self.assertCountEqual(
            list(response.context['form_end_date'].fields['academic_year'].queryset),
            list(self.academic_year_for_suppression_proposal)
        )

    def test_post_request(self):
        response = self.client.post(self.url, data=self.form_data)

        redirected_url = reverse("learning_unit", args=[self.learning_unit_year.id])
        self.assertRedirects(response, redirected_url, fetch_redirect_response=False)

        a_proposal_learning_unit = proposal_learning_unit.find_by_learning_unit_year(self.learning_unit_year)
        self.assertTrue(a_proposal_learning_unit)
        self.assertEqual(a_proposal_learning_unit.author, self.person)

        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertIn(
            _("You proposed a modification of type %(type)s for the learning unit %(acronym)s.") % {
                'type': proposal_type.ProposalType.SUPPRESSION.value,
                'acronym': self.learning_unit_year.acronym
            },
            list(messages)
        )

        self.learning_unit.refresh_from_db()
        self.assertEqual(self.learning_unit.end_year, self.academic_year_for_suppression_proposal.first())


class TestLearningUnitProposalSearch(TestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearFactory.produce(number_past=3, number_future=10)
        cls.person = person_factory.PersonWithPermissionsFactory("can_propose_learningunit", "can_access_learningunit")
        ac_years = AcademicYearFactory.produce_in_future(quantity=3)
        cls.an_entity = EntityFactory()
        cls.entity_version = EntityVersionFactory(entity=cls.an_entity, entity_type=entity_type.SCHOOL,
                                                  start_date=ac_years[0].start_date,
                                                  end_date=ac_years[1].end_date)
        cls.person_entity = PersonEntityFactory(person=cls.person, entity=cls.an_entity, with_child=True)
        cls.proposals = [_create_proposal_learning_unit("LOSIS1211"),
                         _create_proposal_learning_unit("LOSIS1212"),
                         _create_proposal_learning_unit("LOSIS1213")]
        for proposal in cls.proposals:
            PersonEntityFactory(person=cls.person, entity=proposal.entity)

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_learning_units_proposal_search(self):
        url = reverse("learning_units_proposal")
        response = self.client.get(url, data={'acronym': self.proposals[0].learning_unit_year.acronym})

        self.assertEqual(response.context['learning_units_count'], 1)

    def test_learning_units_proposal_search_by_tutor(self):
        proposal = _create_proposal_learning_unit("LOSIS1214")
        tutor = TutorFactory(person=self.person)
        attribution = AttributionNewFactory(tutor=tutor)
        learning_unit_component = LearningComponentYearFactory(learning_unit_year=proposal.learning_unit_year)
        AttributionChargeNewFactory(attribution=attribution,
                                    learning_component_year=learning_unit_component)
        url = reverse("learning_units_proposal")
        response = self.client.get(url, data={'tutor': self.person.first_name})
        self.assertEqual(response.context['learning_units_count'], 1)

    def test_learning_units_proposal_force_state_available_choices_as_faculty_manager(self):
        url = reverse("learning_units_proposal")
        self.person.user.groups.add(FacultyManagerGroupFactory())
        response = self.client.get(url, data={'acronym': self.proposals[0].learning_unit_year.acronym})
        state_choices = response.context['form_proposal_state'].fields['state'].choices
        self.assertEqual(state_choices, list(LimitedProposalState.choices()))

    def test_learning_units_proposal_force_state_available_choices_as_central_manager(self):
        url = reverse("learning_units_proposal")
        self.person.user.groups.add(CentralManagerGroupFactory())
        response = self.client.get(url, data={'acronym': self.proposals[0].learning_unit_year.acronym})
        state_choices = response.context['form_proposal_state'].fields['state'].choices
        self.assertEqual(state_choices, list(ProposalState.choices()))


class TestGroupActionsOnProposals(TestCase):
    @classmethod
    def setUpTestData(cls):
        AcademicYearFactory.produce(number_past=3, number_future=10)
        cls.person = person_factory.PersonWithPermissionsFactory("can_access_learningunit")
        cls.proposals = [_create_proposal_learning_unit("LOSIS1211"),
                         _create_proposal_learning_unit("LOSIS1212"),
                         _create_proposal_learning_unit("LOSIS1213")]
        cls.url = reverse("learning_units_proposal")
        AcademicYearFactory.produce_in_future(quantity=3)

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_when_no_proposals_selected(self):
        response = self.client.post(self.url, data={"action": ACTION_BACK_TO_INITIAL}, follow=True)
        messages = [str(message) for message in response.context["messages"]]
        self.assertIn(_("No proposals was selected."), messages)

    @mock.patch("base.business.learning_unit_proposal.cancel_proposals_and_send_report",
                side_effect=lambda proposals, author, research_criteria: {})
    def test_when_action_is_back_to_initial(self, mock_cancel_proposals):
        post_data = {
            "action": ACTION_BACK_TO_INITIAL,
            "selected_action": [self.proposals[0].learning_unit_year.acronym]
        }
        self.client.post(self.url, data=post_data, follow=True)

        proposals, author, research_criteria = mock_cancel_proposals.call_args[0]
        self.assertEqual(list(proposals), [self.proposals[0]])
        self.assertEqual(author, self.person)
        self.assertFalse(research_criteria)

    @mock.patch("base.business.learning_unit_proposal.consolidate_proposals_and_send_report",
                side_effect=lambda proposals, author, research_criteria: {})
    def test_when_action_is_consolidate(self, mock_consolidate):
        post_data = {
            "action": ACTION_CONSOLIDATE,
            "selected_action": [self.proposals[0].learning_unit_year.acronym]
        }
        self.client.post(self.url, data=post_data, follow=True)

        proposals, author, research_criteria = mock_consolidate.call_args[0]
        self.assertEqual(list(proposals), [self.proposals[0]])
        self.assertEqual(author, self.person)
        self.assertFalse(research_criteria)

    @mock.patch("base.business.learning_unit_proposal.force_state_of_proposals",
                side_effect=lambda proposals, author, research_criteria: {})
    def test_when_action_is_force_state_but_no_new_state(self, mock_force_state):
        post_data = {
            "action": ACTION_FORCE_STATE,
            "selected_action": [self.proposals[0].learning_unit_year.acronym]
        }
        self.client.post(self.url, data=post_data, follow=True)

        self.assertFalse(mock_force_state.called)

    @mock.patch("base.business.learning_unit_proposal.force_state_of_proposals",
                side_effect=lambda proposals, author, research_criteria: {})
    def test_when_action_is_force_state(self, mock_force_state):
        post_data = {
            "action": ACTION_FORCE_STATE,
            "selected_action": [self.proposals[0].learning_unit_year.acronym,
                                self.proposals[2].learning_unit_year.acronym],
            "state": proposal_state.ProposalState.ACCEPTED.name
        }
        self.client.post(self.url, data=post_data, follow=True)

        proposals, author, new_state = mock_force_state.call_args[0]
        self.assertCountEqual(list(proposals), [self.proposals[0], self.proposals[2]])
        self.assertEqual(author, self.person)
        self.assertEqual(new_state, proposal_state.ProposalState.ACCEPTED.name)


@override_flag('learning_unit_proposal_delete', active=True)
class TestLearningUnitProposalCancellation(TestCase):
    @classmethod
    def setUpTestData(cls):
        create_current_academic_year()
        cls.person = person_factory.FacultyManagerForUEFactory("can_propose_learningunit")
        cls.permission = Permission.objects.get(codename="can_propose_learningunit")

    def setUp(self):
        self.learning_unit_proposal = _create_proposal_learning_unit("LOSIS1211")
        self.learning_unit_year = self.learning_unit_proposal.learning_unit_year
        self.person_entity = PersonEntityFactory(
            person=self.person,
            entity=self.learning_unit_year.learning_container_year.requirement_entity
        )
        self.url = reverse('learning_unit_cancel_proposal', args=[self.learning_unit_year.id])
        self.client.force_login(self.person.user)

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_user_has_not_permission(self):
        self.person.user.user_permissions.remove(self.permission)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_with_non_existent_learning_unit_year(self):
        self.learning_unit_year.delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTemplateUsed(response, "page_not_found.html")

    def test_with_none_person(self):
        user = UserFactory()
        user.user_permissions.add(self.permission)
        self.client.force_login(user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTemplateUsed(response, "page_not_found.html")

    def test_with_no_proposal(self):
        self.learning_unit_proposal.delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTemplateUsed(response, "page_not_found.html")

    def test_with_proposal_of_state_different_than_faculty(self):
        self.learning_unit_proposal.state = proposal_state.ProposalState.CENTRAL.name
        self.learning_unit_proposal.save()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_user_not_linked_to_current_requirement_entity(self):
        self.person_entity.delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_context_after_valid_get_request(self):
        response = self.client.get(self.url)

        redirected_url = reverse('learning_unit', args=[self.learning_unit_year.id])
        self.assertRedirects(response, redirected_url, fetch_redirect_response=False)

        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertIn(_("Proposal %(acronym)s (%(academic_year)s) successfully canceled.") % {
            "acronym": self.learning_unit_year.acronym,
            "academic_year": self.learning_unit_year.academic_year
        }, messages)

    def test_models_after_cancellation_of_proposal(self):
        _modify_learning_unit_year_data(self.learning_unit_year)
        _modify_entities_linked_to_learning_container_year(self.learning_unit_year.learning_container_year)
        self.client.get(self.url)

        self.learning_unit_year.refresh_from_db()
        self.learning_unit_year.learning_container_year.refresh_from_db()
        initial_data = self.learning_unit_proposal.initial_data
        self.assertTrue(_test_attributes_equal(self.learning_unit_year, initial_data["learning_unit_year"]))
        self.assertTrue(_test_attributes_equal(self.learning_unit_year.learning_unit, initial_data["learning_unit"]))
        self.assertTrue(_test_attributes_equal(self.learning_unit_year.learning_container_year,
                                               initial_data["learning_container_year"]))


def _test_attributes_equal(obj, attribute_values_dict):
    for key, value in attribute_values_dict.items():
        attr_value = getattr(obj, key)
        foreign_key_fields = [
            "campus", "language", 'requirement_entity', 'allocation_entity',
            'additional_entity_1', 'additional_entity_2'
        ]
        if key == "credits":
            if float(attr_value) != float(value):
                return False
        elif attr_value and key in foreign_key_fields:
            if attr_value.pk != value:
                return False
        elif attr_value != value:
            return False
    return True


def _create_proposal_learning_unit(acronym):
    a_learning_unit_year = LearningUnitYearFactory(
        acronym=acronym,
        subtype=learning_unit_year_subtypes.FULL,
        learning_container_year__requirement_entity=EntityVersionFactory().entity,
    )
    learning_component_lecturing = LearningComponentYearFactory(
        learning_unit_year=a_learning_unit_year,
        type=learning_component_year_type.LECTURING
    )
    learning_component_practical = LearningComponentYearFactory(
        learning_unit_year=a_learning_unit_year,
        type=learning_component_year_type.PRACTICAL_EXERCISES)

    container_year = a_learning_unit_year.learning_container_year
    initial_data = {
        "learning_container_year": {
            "id": container_year.id,
            "acronym": a_learning_unit_year.acronym,
            "common_title": a_learning_unit_year.specific_title,
            "common_title_english": a_learning_unit_year.specific_title_english,
            "container_type": container_year.container_type,
            "in_charge": container_year.in_charge,
            "requirement_entity": container_year.requirement_entity.id,
            "allocation_entity": None,
            "additional_entity_1": None,
            "additional_entity_2": None,
        },
        "learning_unit_year": {
            "id": a_learning_unit_year.id,
            "acronym": a_learning_unit_year.acronym,
            "specific_title": a_learning_unit_year.specific_title,
            "specific_title_english": a_learning_unit_year.specific_title_english,
            "internship_subtype": a_learning_unit_year.internship_subtype,
            "credits": float(a_learning_unit_year.credits),
            "language": a_learning_unit_year.language.pk,
            "campus": a_learning_unit_year.campus.id,
            "periodicity": a_learning_unit_year.periodicity
        },
        "learning_unit": {
            "id": a_learning_unit_year.learning_unit.id,
        },
        "learning_component_years": [
            {"id": learning_component_lecturing.id, "planned_classes": learning_component_lecturing.planned_classes,
             "hourly_volume_partial_q1": learning_component_lecturing.hourly_volume_partial_q1,
             "hourly_volume_partial_q2": learning_component_lecturing.hourly_volume_partial_q2,
             "hourly_volume_total_annual": learning_component_lecturing.hourly_volume_total_annual
             },
            {"id": learning_component_practical.id, "planned_classes": learning_component_practical.planned_classes,
             "hourly_volume_partial_q1": learning_component_practical.hourly_volume_partial_q1,
             "hourly_volume_partial_q2": learning_component_practical.hourly_volume_partial_q2,
             "hourly_volume_total_annual": learning_component_practical.hourly_volume_total_annual
             }
        ]

    }

    return ProposalLearningUnitFactory(learning_unit_year=a_learning_unit_year,
                                       type=proposal_type.ProposalType.MODIFICATION.name,
                                       state=proposal_state.ProposalState.FACULTY.name,
                                       initial_data=initial_data,
                                       entity=container_year.requirement_entity)


def _modify_learning_unit_year_data(a_learning_unit_year):
    a_learning_unit_year.specific_title = "New title"
    a_learning_unit_year.specific_title_english = "New english title"
    a_learning_unit_year.acronym = "LNEW456"
    a_learning_unit_year.credits = 123
    a_learning_unit_year.language = LanguageFactory()
    a_learning_unit_year.save()

    a_learning_container = a_learning_unit_year.learning_container_year
    a_learning_container.campus = CampusFactory()
    a_learning_container.save()


def _modify_entities_linked_to_learning_container_year(a_learning_container_year):
    a_learning_container_year.requirement_entity = EntityFactory()
    a_learning_container_year.save()


@override_flag('learning_unit_proposal_update', active=True)
class TestEditProposal(TestCase):
    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        cls.academic_years = AcademicYearFactory.produce_in_future(quantity=5)
        cls.current_academic_year = cls.academic_years[0]
        end_year = AcademicYearFactory(year=cls.current_academic_year.year + 10)
        generate_modification_transformation_proposal_calendars(cls.academic_years)
        generate_creation_or_end_date_proposal_calendars(cls.academic_years)
        cls.language = FrenchLanguageFactory()
        cls.organization = organization_factory.OrganizationFactory(type=organization_type.MAIN)
        cls.campus = campus_factory.CampusFactory(organization=cls.organization, is_administration=True)
        cls.entity = EntityFactory(organization=cls.organization)
        cls.entity_version = EntityVersionFactory(entity=cls.entity, entity_type=entity_type.FACULTY,
                                                  start_date=today.replace(year=1900),
                                                  end_date=None)

        cls.generated_container = GenerateContainer(cls.current_academic_year, end_year)
        cls.generated_container_first_year = cls.generated_container.generated_container_years[1]
        cls.learning_unit_year = cls.generated_container_first_year.learning_unit_year_full

        cls.person = person_factory.FacultyManagerForUEFactory("can_edit_learning_unit_proposal")
        cls.requirement_entity_of_luy = cls.generated_container_first_year.requirement_entity_container_year
        PersonEntityFactory(entity=cls.requirement_entity_of_luy, person=cls.person)
        cls.person_entity = PersonEntityFactory(person=cls.person, entity=cls.entity)

        cls.url = reverse(update_learning_unit_proposal, args=[cls.learning_unit_year.id])
        cls.academic_year_for_suppression_proposal = AcademicYear.objects.filter(
            year=cls.learning_unit_year.academic_year.year - 1)

    def setUp(self):
        self.proposal = ProposalLearningUnitFactory(learning_unit_year=self.learning_unit_year,
                                                    state=ProposalState.FACULTY.name,
                                                    folder_id=1,
                                                    entity=self.entity,
                                                    type=proposal_type.ProposalType.MODIFICATION.name)
        self.client.force_login(self.person.user)

    def test_edit_proposal_get_no_permission(self):
        person = person_factory.PersonFactory()
        self.client.force_login(person.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_edit_proposal_get_regular_user_with_permission(self):
        person = person_factory.PersonWithPermissionsFactory("can_edit_learning_unit_proposal")
        self.client.force_login(person.user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_edit_proposal_get_as_faculty_manager(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, 'learning_unit/proposal/update_modification.html')
        self.assertIsInstance(response.context['form_proposal'], ProposalLearningUnitForm)

    def test_edit_proposal_get_as_central_manager_with_instance(self):
        central_manager = person_factory.CentralManagerForUEFactory("can_edit_learning_unit_proposal")
        PersonEntityFactory(person=central_manager, entity=self.requirement_entity_of_luy)
        self.client.logout()
        self.client.force_login(central_manager.user)
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, 'learning_unit/proposal/update_modification.html')
        self.assertIsInstance(response.context['form_proposal'], ProposalLearningUnitForm)
        self.assertEqual(response.context['form_proposal'].initial['state'], str(ProposalState.FACULTY.name))

    def get_valid_data(self):
        return {
            'acronym_0': 'L',
            'acronym_1': 'TAU2000',
            "subtype": learning_unit_year_subtypes.FULL,
            "container_type": learning_container_year_types.COURSE,
            "academic_year": self.current_academic_year.id,
            "status": True,
            "credits": "5",
            "campus": self.campus.id,
            "common_title": "Common UE title",
            "language": self.language.pk,
            "periodicity": learning_unit_year_periodicity.ANNUAL,
            "entity": self.entity_version.id,
            "folder_id": 1,
            'requirement_entity': self.entity_version.id,
            'allocation_entity': self.entity_version.id,
            'additional_entity_1': '',

            # Learning component year data model form
            'component-TOTAL_FORMS': '2',
            'component-INITIAL_FORMS': '0',
            'component-MAX_NUM_FORMS': '2',
            'component-0-hourly_volume_total_annual': 20,
            'component-0-hourly_volume_partial_q1': 10,
            'component-0-hourly_volume_partial_q2': 10,
            'component-0-planned_classes': 1,
            'component-1-hourly_volume_total_annual': 20,
            'component-1-hourly_volume_partial_q1': 10,
            'component-1-hourly_volume_partial_q2': 10,
            'component-1-planned_classes': 1,
        }

    def get_modify_data(self):
        modifydict = dict(self.get_valid_data())
        modifydict["state"] = ProposalState.CENTRAL.value
        return modifydict

    def get_faulty_data(self):
        faultydict = dict(self.get_valid_data())
        faultydict["state"] = "bad_choice"
        return faultydict

    def test_edit_proposal_post_as_faculty_manager(self):
        initial_data = copy_learning_unit_data(self.learning_unit_year)
        self.proposal.initial_data = initial_data
        request_factory = RequestFactory()
        request = request_factory.post(self.url, data=self.get_modify_data())

        request.user = self.person.user
        request.session = 'session'
        request._messages = FallbackStorage(request)

        update_learning_unit_proposal(request, self.learning_unit_year.id)

        msg = [m.message for m in get_messages(request)]
        msg_level = [m.level for m in get_messages(request)]
        self.assertIn(messages.SUCCESS, msg_level, msg)
        self.assertEqual(len(msg), 1)

        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.state, 'FACULTY')

    def test_edit_proposal_post_wrong_data(self):
        self.person.user.groups.add(CentralManagerGroupFactory())

        response = self.client.post(self.url, data=self.get_faulty_data())

        self.assertTemplateUsed(response, 'learning_unit/proposal/update_modification.html')
        self.assertIsInstance(response.context['form_proposal'], ProposalLearningUnitForm)

        form = response.context['form_proposal']
        self.assertEqual(len(form.errors), 1)

        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.state, ProposalState.FACULTY.name)

    def test_edit_suppression_proposal_get(self):
        self.proposal.type = ProposalType.SUPPRESSION.name
        self.proposal.save()

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, 'learning_unit/proposal/update_suppression.html')
        self.assertIsInstance(response.context['form_end_date'], LearningUnitProposalEndDateForm)
        self.assertCountEqual(
            list(response.context['form_end_date'].fields['academic_year'].queryset),
            list(self.academic_year_for_suppression_proposal)
        )
        self.assertIsInstance(response.context['form_proposal'], ProposalLearningUnitForm)

    def test_edit_suppression_proposal_post(self):
        self.proposal.type = ProposalType.SUPPRESSION.name
        self.proposal.save()

        request_factory = RequestFactory()
        request = request_factory.post(self.url,
                                       data={"academic_year": self.academic_year_for_suppression_proposal.first().id,
                                             "entity": self.entity_version.id,
                                             "folder_id": 12})

        request.user = self.person.user
        request.session = 'session'
        request._messages = FallbackStorage(request)

        update_learning_unit_proposal(request, self.learning_unit_year.id)

        msg = [m.message for m in get_messages(request)]
        msg_level = [m.level for m in get_messages(request)]
        self.assertEqual(len(msg), 1)
        self.assertIn(messages.SUCCESS, msg_level)

        self.proposal.refresh_from_db()
        self.assertEqual(self.proposal.folder_id, 12)

    def test_edit_suppression_proposal_wrong_post(self):
        self.proposal.type = ProposalType.SUPPRESSION.name
        self.proposal.save()
        response = self.client.post(self.url, data={"academic_year": self.academic_years[3].id,
                                                    "entity": self.entity_version.id})
        self.assertEqual(self.url, response.request['PATH_INFO'])


class TestLearningUnitProposalDisplay(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.language_pt = LanguageFactory(code='PT', name="Portugais")
        cls.language_it = LanguageFactory(code='IT', name="Italien")
        cls.campus = CampusFactory()
        cls.academic_year = create_current_academic_year()
        cls.l_container_year = LearningContainerYearFactory(
            acronym="LBIR1212",
            academic_year=cls.academic_year,
        )
        cls.learning_unit = LearningUnitFactory(learning_container=cls.l_container_year.learning_container)

        cls.learning_unit_yr = LearningUnitYearFactory(
            acronym="LBIR1212",
            learning_unit=cls.learning_unit,
            learning_container_year=cls.l_container_year,
            academic_year=cls.academic_year,
            subtype=learning_unit_year_subtypes.FULL,
            status=True,
            quadrimester="Q3",
            credits=4,
            campus=cls.campus,
            language=cls.language_pt,
            periodicity=learning_unit_year_periodicity.BIENNIAL_EVEN
        )

        cls.proposal_learning_unit = ProposalLearningUnitFactory(learning_unit_year=cls.learning_unit_yr)
        cls.initial_credits = 3.0
        cls.initial_quadrimester = 'Q1'
        cls.initial_language = cls.language_it.pk
        cls.initial_periodicity = learning_unit_year_periodicity.ANNUAL
        cls.initial_data_learning_unit_year = {'credits': cls.initial_credits, 'periodicity': cls.initial_periodicity}

        cls.initial_language_en = cls.language_it
        end_year = AcademicYearFactory(year=cls.academic_year.year + 1)
        cls.generator_learning_container = GenerateContainer(start_year=cls.academic_year, end_year=end_year)
        cls.l_container_year_with_entities = cls.generator_learning_container.generated_container_years[0]
        organization_main = OrganizationFactory(type=organization_type.MAIN)
        cls.entity_from_main_organization = EntityFactory(organization=organization_main)
        cls.entity_version = EntityVersionFactory(entity=cls.entity_from_main_organization)
        organization_not_main = OrganizationFactory(type=organization_type.ACADEMIC_PARTNER)
        cls.entity_from_not_main_organization = EntityFactory(organization=organization_not_main)
        cls.entity_version_not_main = EntityVersionFactory(entity=cls.entity_from_not_main_organization)

    def test_is_foreign_key(self):
        current_data = {"language{}".format(proposal_business.END_FOREIGN_KEY_NAME): self.language_it.pk}
        self.assertTrue(proposal_business._is_foreign_key("language", current_data))

    def test_is_not_foreign_key(self):
        current_data = {"credits": self.language_it.pk}
        self.assertFalse(proposal_business._is_foreign_key("credits", current_data))

    def test_check_differences(self):
        proposal = ProposalLearningUnitFactory()
        proposal.initial_data = {'learning_unit_year': {
            'credits': self.initial_credits
        }}
        proposal.learning_unit_year.credits = self.learning_unit_yr.credits

        differences = proposal_business.get_difference_of_proposal(proposal, proposal.learning_unit_year)
        self.assertEqual(float(differences.get('credits')), self.initial_credits)

    def test_get_the_old_value(self):
        differences = proposal_business._get_the_old_value('credits',
                                                           {"credits": self.initial_credits + 1},
                                                           {'credits': self.initial_credits})
        self.assertEqual(differences, "{}".format(self.initial_credits))

    def test_get_the_old_value_no_initial_value(self):
        differences = proposal_business._get_the_old_value('credits',
                                                           {"credits": self.initial_credits + 1},
                                                           {})
        self.assertEqual(differences, proposal_business.NO_PREVIOUS_VALUE)

    def test_get_the_old_value_for_foreign_key(self):
        initial_data_learning_unit_year = {'language': self.language_pt.pk}
        current_data = {"language_id": self.language_it.pk}
        differences = proposal_business._get_the_old_value('language',
                                                           current_data,
                                                           initial_data_learning_unit_year)
        self.assertEqual(differences, str(self.language_pt))

    def test_get_the_old_value_for_foreign_key_no_previous_value(self):
        initial_data = {"language": None}
        current_data = {"language_id": self.language_it.pk}

        differences = proposal_business._get_the_old_value('language', current_data, initial_data)
        self.assertEqual(differences, proposal_business.NO_PREVIOUS_VALUE)

        initial_data = {}
        differences = proposal_business._get_the_old_value('language', current_data, initial_data)
        self.assertEqual(differences, proposal_business.NO_PREVIOUS_VALUE)

    def test_get_the_old_value_with_translation(self):
        key = proposal_business.VALUES_WHICH_NEED_TRANSLATION[0]
        initial_data = {key: learning_unit_year_periodicity.ANNUAL}
        current_data = {key: learning_unit_year_periodicity.BIENNIAL_EVEN}
        differences = proposal_business._get_the_old_value(key, current_data, initial_data)
        self.assertEqual(differences, _(learning_unit_year_periodicity.ANNUAL))

    def test_get_str_representing_old_data_from_foreign_key(self):
        differences = proposal_business._get_str_representing_old_data_from_foreign_key('campus', self.campus.id)
        self.assertEqual(differences, str(self.campus.name))

    def test_get_str_representing_old_data_from_foreign_key_equals_no_value(self):
        differences = proposal_business._get_str_representing_old_data_from_foreign_key(
            'campus',
            proposal_business.NO_PREVIOUS_VALUE)
        self.assertEqual(differences, proposal_business.NO_PREVIOUS_VALUE)

    def test_get_old_value_of_foreign_key_for_campus(self):
        differences = proposal_business._get_old_value_of_foreign_key('campus', self.campus.id)
        self.assertEqual(differences, str(self.campus.name))

    def test_get_old_value_of_foreign_key_for_language(self):
        differences = proposal_business._get_old_value_of_foreign_key('language', self.language_it.pk)
        self.assertEqual(differences, str(self.language_it))

    def test_get_old_value_of_foreign_key_for_additional_requirement_entity_main_organization(self):
        differences = proposal_business._get_old_value_of_foreign_key('ADDITIONAL_REQUIREMENT_ENTITY_1',
                                                                      self.entity_from_main_organization.pk)
        self.assertEqual(differences, str(self.entity_from_main_organization.most_recent_entity_version.acronym))

    def test_get_old_value_of_foreign_key_for_additional_requirement_entity_not_main_organization(self):
        differences = proposal_business._get_old_value_of_foreign_key('ADDITIONAL_REQUIREMENT_ENTITY_1',
                                                                      self.entity_from_not_main_organization.pk)
        self.assertEqual(differences, str(self.entity_from_not_main_organization.most_recent_entity_version.title))

    def test_get_status_initial_value(self):
        self.assertEqual(proposal_business._get_status_initial_value(True),
                         proposal_business.LABEL_ACTIVE)
        self.assertEqual(proposal_business._get_status_initial_value(False),
                         proposal_business.LABEL_INACTIVE)

    def test_get_old_value_for_periodicity(self):
        differences = proposal_business._get_the_old_value('periodicity',
                                                           {"periodicity": self.learning_unit_yr.periodicity},
                                                           {'periodicity': self.initial_periodicity})
        self.assertEqual(differences,
                         dict(learning_unit_year_periodicity.PERIODICITY_TYPES)[self.initial_periodicity])


@override_flag('learning_unit_proposal_delete', active=True)
class TestCreationProposalCancel(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.a_person_central_manager = person_factory.CentralManagerForUEFactory(
            'can_propose_learningunit', 'can_access_learningunit'
        )

    def setUp(self):
        self.client.force_login(self.a_person_central_manager.user)

    @mock.patch('base.views.learning_units.perms.business_perms.is_eligible_for_cancel_of_proposal',
                side_effect=lambda *args: True)
    @mock.patch('base.utils.send_mail.send_mail_cancellation_learning_unit_proposals')
    def test_cancel_proposal_of_learning_unit(self, mock_send_mail, mock_perms):
        a_proposal = _create_proposal_learning_unit("LOSIS1211")
        luy = a_proposal.learning_unit_year
        url = reverse('learning_unit_cancel_proposal', args=[luy.id])

        response = self.client.post(url, data={})

        redirected_url = reverse('learning_unit', args=[luy.id])
        msgs = [str(message) for message in get_messages(response.wsgi_request)]

        self.assertRedirects(response, redirected_url, fetch_redirect_response=False)
        self.assertEqual(len(msgs), 2)
        self.assertTrue(mock_send_mail.called)
        self.assertTrue(mock_perms.called)
