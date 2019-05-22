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
import json
from unittest import mock

from django.contrib import messages
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponseForbidden, HttpResponseNotFound, HttpResponse
from django.test import TestCase, RequestFactory
from django.urls import reverse
from waffle.testutils import override_flag

from base.forms.learning_unit.entity_form import EntityContainerBaseForm
from base.forms.learning_unit.learning_unit_create import LearningUnitModelForm, LearningUnitYearModelForm, \
    LearningContainerYearModelForm
from base.models.enums import learning_unit_year_periodicity, learning_container_year_types, \
    learning_unit_year_subtypes, \
    entity_container_year_link_type, vacant_declaration_type, attribution_procedure, entity_type, organization_type
from base.models.enums.organization_type import MAIN, ACADEMIC_PARTNER
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory, get_current_year
from base.tests.factories.business.learning_units import LearningUnitsMixin, GenerateContainer, GenerateAcademicYear
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.user import UserFactory, SuperUserFactory
from base.tests.forms.test_edition_form import get_valid_formset_data
from base.views.learning_unit import learning_unit_components
from base.views.learning_units.update import learning_unit_edition_end_date, learning_unit_volumes_management, \
    update_learning_unit, _get_learning_units_for_context
from reference.tests.factories.country import CountryFactory


@override_flag('learning_unit_update', active=True)
class TestLearningUnitEditionView(TestCase, LearningUnitsMixin):

    def setUp(self):
        super().setUp()
        self.user = UserFactory(username="YodaTheJediMaster")
        self.person = PersonFactory(user=self.user)
        self.permission = Permission.objects.get(codename="can_edit_learningunit_date")
        self.person.user.user_permissions.add(self.permission)
        self.client.force_login(self.user)

        self.setup_academic_years()
        self.learning_unit = self.setup_learning_unit(self.starting_academic_year.year)
        self.learning_container_year = self.setup_learning_container_year(
            academic_year=self.starting_academic_year,
            container_type=learning_container_year_types.COURSE
        )
        self.learning_unit_year = self.setup_learning_unit_year(
            self.starting_academic_year,
            self.learning_unit,
            self.learning_container_year,
            learning_unit_year_subtypes.FULL,
            learning_unit_year_periodicity.ANNUAL
        )

        self.a_superuser = SuperUserFactory()
        self.a_superperson = PersonFactory(user=self.a_superuser)

    def test_view_learning_unit_edition_permission_denied(self):
        from base.views.learning_units.update import learning_unit_edition_end_date

        response = self.client.get(reverse(learning_unit_edition_end_date, args=[self.learning_unit_year.id]))
        self.assertEqual(response.status_code, 403)

    @mock.patch('base.business.learning_units.perms.is_eligible_for_modification_end_date')
    def test_view_learning_unit_edition_get(self, mock_perms):
        mock_perms.return_value = True
        response = self.client.get(reverse(learning_unit_edition_end_date, args=[self.learning_unit_year.id]))
        self.assertTemplateUsed(response, "learning_unit/simple/update_end_date.html")

    @mock.patch('base.business.learning_units.perms.is_eligible_for_modification_end_date')
    def test_view_learning_unit_edition_post(self, mock_perms):
        mock_perms.return_value = True

        request_factory = RequestFactory()

        form_data = {"academic_year": self.starting_academic_year.pk}
        request = request_factory.post(reverse('learning_unit_edition', args=[self.learning_unit_year.id]),
                                       data=form_data)
        request.user = self.a_superuser
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        learning_unit_edition_end_date(request, self.learning_unit_year.id)

        msg_level = [m.level for m in get_messages(request)]
        msg = [m.message for m in get_messages(request)]
        self.assertEqual(len(msg), 1)
        self.assertIn(messages.SUCCESS, msg_level)

    @mock.patch('base.business.learning_units.perms.is_eligible_for_modification_end_date')
    def test_view_learning_unit_edition_template(self, mock_perms):
        mock_perms.return_value = True
        url = reverse("learning_unit_edition", args=[self.learning_unit_year.id])
        response = self.client.get(url)
        self.assertTemplateUsed(response, "learning_unit/simple/update_end_date.html")


@override_flag('learning_unit_update', active=True)
class TestEditLearningUnit(TestCase):
    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        an_academic_year = create_current_academic_year()
        learning_container_year = LearningContainerYearFactory(
            academic_year=an_academic_year,
            container_type=learning_container_year_types.COURSE,
            type_declaration_vacant=vacant_declaration_type.DO_NOT_ASSIGN,
        )

        cls.learning_unit_year = LearningUnitYearFactory(
            learning_container_year=learning_container_year,
            acronym="LOSIS4512",
            academic_year=an_academic_year,
            subtype=learning_unit_year_subtypes.FULL,
            attribution_procedure=attribution_procedure.INTERNAL_TEAM,
            credits=15,
            campus=CampusFactory(organization=OrganizationFactory(type=organization_type.MAIN)),
            internship_subtype=None,
        )

        cls.partim_learning_unit = LearningUnitYearFactory(
            learning_container_year=learning_container_year,
            acronym="LOSIS4512A",
            academic_year=an_academic_year,
            subtype=learning_unit_year_subtypes.PARTIM,
            credits=10,
            campus=CampusFactory(organization=OrganizationFactory(type=organization_type.MAIN))
        )

        cls.requirement_entity_container = EntityContainerYearFactory(
            learning_container_year=learning_container_year, type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        cls.requirement_entity_container.entity.organization.type = organization_type.MAIN
        cls.requirement_entity_container.entity.organization.save()
        cls.requirement_entity = EntityVersionFactory(entity=cls.requirement_entity_container.entity,
                                                      entity_type=entity_type.SCHOOL,
                                                      start_date=today.replace(year=1900),
                                                      end_date=None)

        cls.allocation_entity_container = EntityContainerYearFactory(
            learning_container_year=learning_container_year, type=entity_container_year_link_type.ALLOCATION_ENTITY)
        cls.allocation_entity = EntityVersionFactory(entity=cls.allocation_entity_container.entity,
                                                     start_date=today.replace(year=1900),
                                                     end_date=None)

        cls.additional_entity_container_1 = EntityContainerYearFactory(
            learning_container_year=learning_container_year,
            type=entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1)
        cls.additional_entity_1 = EntityVersionFactory(entity=cls.additional_entity_container_1.entity,
                                                       start_date=today.replace(year=1900),
                                                       end_date=None)

        cls.additional_entity_container_2 = EntityContainerYearFactory(
            learning_container_year=learning_container_year,
            type=entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2)
        cls.additional_entity_2 = EntityVersionFactory(entity=cls.additional_entity_container_2.entity,
                                                       start_date=today.replace(year=1900),
                                                       end_date=None)

        cls.person = PersonEntityFactory(entity=cls.requirement_entity_container.entity).person
        cls.user = cls.person.user
        cls.user.user_permissions.add(Permission.objects.get(codename="can_edit_learningunit"),
                                      Permission.objects.get(codename="can_access_learningunit"))
        cls.url = reverse(update_learning_unit, args=[cls.learning_unit_year.id])

    def setUp(self):
        self.client.force_login(self.user)

    def test_user_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_user_has_no_right_to_modify_learning_unit(self):
        user_with_no_rights_to_edit = UserFactory()
        self.client.force_login(user_with_no_rights_to_edit)

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_learning_unit_does_not_exist(self):
        non_existent_learning_unit_year_id = self.learning_unit_year.id + self.partim_learning_unit.id
        url = reverse("edit_learning_unit", args=[non_existent_learning_unit_year_id])

        response = self.client.get(url)

        self.assertTemplateUsed(response, "page_not_found.html")
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_user_is_not_linked_to_a_person(self):
        user = UserFactory()
        user.user_permissions.add(Permission.objects.get(codename="can_edit_learningunit"))
        self.client.force_login(user)

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "page_not_found.html")
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_cannot_modify_past_learning_unit(self):
        past_year = datetime.date.today().year - 2
        past_academic_year = AcademicYearFactory(year=past_year)
        past_learning_container_year = LearningContainerYearFactory(academic_year=past_academic_year,
                                                                    container_type=learning_container_year_types.COURSE)
        past_learning_unit_year = LearningUnitYearFactory(learning_container_year=past_learning_container_year,
                                                          subtype=learning_unit_year_subtypes.FULL)

        url = reverse("edit_learning_unit", args=[past_learning_unit_year.id])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_template_used_for_get_request(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "learning_unit/simple/update.html")
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_context_used_for_get_request(self):
        response = self.client.get(self.url)

        context = response.context
        self.assertEqual(context["learning_unit_year"], self.learning_unit_year)
        self.assertIsInstance(context["learning_unit_form"], LearningUnitModelForm)
        self.assertIsInstance(context["learning_unit_year_form"], LearningUnitYearModelForm)
        self.assertIsInstance(context["learning_container_year_form"], LearningContainerYearModelForm)
        self.assertIsInstance(context["entity_container_form"], EntityContainerBaseForm)

    def test_form_initial_data(self):
        response = self.client.get(self.url)
        context = response.context[-1]
        acronym = self.learning_unit_year.acronym
        # Expected initials form
        expected_initials = {
            'learning_container_year_form': {
                "container_type": self.learning_unit_year.learning_container_year.container_type,
                "common_title": self.learning_unit_year.learning_container_year.common_title,
                "common_title_english": self.learning_unit_year.learning_container_year.common_title_english,
                "team": self.learning_unit_year.learning_container_year.team,
                "is_vacant": self.learning_unit_year.learning_container_year.is_vacant,
                "type_declaration_vacant": self.learning_unit_year.learning_container_year.type_declaration_vacant
            },
            'learning_unit_year_form': {
                "acronym": [acronym[0], acronym[1:]],
                "academic_year": self.learning_unit_year.academic_year.id,
                "status": self.learning_unit_year.status,
                "credits": self.learning_unit_year.credits,
                "specific_title": self.learning_unit_year.specific_title,
                "specific_title_english": self.learning_unit_year.specific_title_english,
                "session": self.learning_unit_year.session,
                "quadrimester": self.learning_unit_year.quadrimester,
                "attribution_procedure": self.learning_unit_year.attribution_procedure,
                "internship_subtype": self.learning_unit_year.internship_subtype,
                "professional_integration": self.learning_unit_year.professional_integration,
                "campus": self.learning_unit_year.campus.pk,
                "language": self.learning_unit_year.language.pk,
                "periodicity": self.learning_unit_year.periodicity
            },
            'learning_unit_form': {
                "faculty_remark": self.learning_unit_year.learning_unit.faculty_remark,
                "other_remark": self.learning_unit_year.learning_unit.other_remark
            }
        }
        for form_name, expected_initial in expected_initials.items():
            initial_data = context[form_name].initial
            self.assertDictEqual(initial_data, expected_initial)

        expected_initials = [
            {'entity': self.requirement_entity.pk},
            {'entity': self.allocation_entity.pk},
            {'entity': self.additional_entity_1.pk},
            {'entity': self.additional_entity_2.pk},
        ]
        entity_container_formset = context['entity_container_form']
        for idx, expected_initial in enumerate(expected_initials):
            initial_data = entity_container_formset.forms[idx].initial
            self.assertDictEqual(initial_data, expected_initial)

    def test_valid_post_request(self):
        credits = 18
        form_data = self._get_valid_form_data()
        form_data['credits'] = credits
        form_data['container_type'] = learning_container_year_types.COURSE
        response = self.client.post(self.url, data=form_data)

        expected_redirection = reverse("learning_unit", args=[self.learning_unit_year.id])
        self.assertRedirects(response, expected_redirection)

        self.learning_unit_year.refresh_from_db()
        self.assertEqual(self.learning_unit_year.credits, credits)

    def _get_valid_form_data(self):
        form_data = {
            "acronym_0": self.learning_unit_year.acronym[0],
            "acronym_1": self.learning_unit_year.acronym[1:],
            "credits": self.learning_unit_year.credits,
            "specific_title": self.learning_unit_year.specific_title,
            "periodicity": learning_unit_year_periodicity.ANNUAL,
            "campus": self.learning_unit_year.campus.pk,
            "language": self.learning_unit_year.language.pk,
            "status": True,

            'requirement_entity-entity': self.requirement_entity.id,
            'allocation_entity-entity': self.requirement_entity.id,
            'additional_requirement_entity_1-entity': '',
            # Learning component year data model form
            'component-TOTAL_FORMS': '2',
            'component-INITIAL_FORMS': '0',
            'component-MAX_NUM_FORMS': '2',
            'component-0-hourly_volume_total_annual': 20,
            'component-0-hourly_volume_partial_q1': 10,
            'component-0-hourly_volume_partial_q2': 10,
            'component-1-hourly_volume_total_annual': 20,
            'component-1-hourly_volume_partial_q1': 10,
            'component-1-hourly_volume_partial_q2': 10,
        }
        return form_data


@override_flag('learning_unit_update', active=True)
class TestLearningUnitVolumesManagement(TestCase):
    def setUp(self):
        self.academic_years = GenerateAcademicYear(start_year=get_current_year(), end_year=get_current_year() + 10)
        self.generate_container = GenerateContainer(start_year=get_current_year(), end_year=get_current_year() + 10)
        self.generated_container_year = self.generate_container.generated_container_years[0]

        self.container_year = self.generated_container_year.learning_container_year
        self.learning_unit_year = self.generated_container_year.learning_unit_year_full
        self.learning_unit_year_partim = self.generated_container_year.learning_unit_year_partim

        self.person = PersonFactory()

        edit_learning_unit_permission = Permission.objects.get(codename="can_edit_learningunit")
        self.person.user.user_permissions.add(edit_learning_unit_permission)

        self.url = reverse('learning_unit_volumes_management', kwargs={
            'learning_unit_year_id': self.learning_unit_year.id,
            'form_type': 'full'
        })

        self.client.force_login(self.person.user)
        self.user = self.person.user

        PersonEntityFactory(entity=self.generate_container.entities[0], person=self.person)

    @mock.patch('base.models.program_manager.is_program_manager')
    def test_learning_unit_volumes_management_get_full_form(self, mock_program_manager):
        mock_program_manager.return_value = True

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, 'learning_unit/volumes_management.html')
        self.assertEqual(response.context['learning_unit_year'], self.learning_unit_year)
        for formset in response.context['formsets'].keys():
            self.assertIn(formset, [self.learning_unit_year, self.learning_unit_year_partim])

        # Check that we display only the current learning_unit_year in the volumes management page (not all the family)
        self.assertListEqual(
            response.context['learning_units'],
            [self.learning_unit_year, self.learning_unit_year_partim]
        )

    @mock.patch('base.models.program_manager.is_program_manager')
    def test_learning_unit_volumes_management_get_simple_form(self, mock_program_manager):
        mock_program_manager.return_value = True

        simple_url = reverse('learning_unit_volumes_management', kwargs={
            'learning_unit_year_id': self.learning_unit_year.id,
            'form_type': 'simple'
        })

        response = self.client.get(simple_url)

        self.assertTemplateUsed(response, 'learning_unit/volumes_management.html')
        self.assertEqual(response.context['learning_unit_year'], self.learning_unit_year)
        for formset in response.context['formsets'].keys():
            self.assertIn(formset, [self.learning_unit_year, self.learning_unit_year_partim])

        # Check that we display only the current learning_unit_year in the volumes management page (not all the family)
        self.assertListEqual(response.context['learning_units'], [self.learning_unit_year])

    @mock.patch('base.models.program_manager.is_program_manager')
    def test_learning_unit_volumes_management_post_full_form(self, mock_program_manager):
        mock_program_manager.return_value = True

        request_factory = RequestFactory()
        data = get_valid_formset_data(self.learning_unit_year.acronym)
        data.update(get_valid_formset_data(self.learning_unit_year_partim.acronym, is_partim=True))

        request = request_factory.post(reverse(learning_unit_volumes_management,
                                               kwargs={
                                                   'learning_unit_year_id': self.learning_unit_year.id,
                                                   'form_type': 'full'
                                               }),
                                       data=data)

        request.user = self.user
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        response = learning_unit_volumes_management(request, learning_unit_year_id=self.learning_unit_year.id,
                                                    form_type="full")

        msg_level = [m.level for m in get_messages(request)]
        msg = [m.message for m in get_messages(request)]
        self.assertEqual(len(msg), 1)
        self.assertIn(messages.SUCCESS, msg_level)
        self.assertEqual(response.url, reverse(learning_unit_components, args=[self.learning_unit_year.id]))

        for generated_container_year in self.generate_container:
            learning_component_year = generated_container_year.learning_component_cm_full
            self.check_postponement(learning_component_year)

    @mock.patch('base.models.program_manager.is_program_manager')
    def test_learning_unit_volumes_management_post_simple_form(self, mock_program_manager):
        mock_program_manager.return_value = True

        request_factory = RequestFactory()
        data = get_valid_formset_data(self.learning_unit_year.acronym)
        data.update(get_valid_formset_data(self.learning_unit_year_partim.acronym, is_partim=True))

        request = request_factory.post(reverse(learning_unit_volumes_management,
                                               kwargs={
                                                   'learning_unit_year_id': self.learning_unit_year.id,
                                                   'form_type': 'simple'
                                               }),
                                       data=data)

        request.user = self.user
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        response = learning_unit_volumes_management(request, learning_unit_year_id=self.learning_unit_year.id,
                                                    form_type="simple")

        msg_level = [m.level for m in get_messages(request)]
        msg = [m.message for m in get_messages(request)]
        self.assertEqual(len(msg), 1)
        self.assertIn(messages.SUCCESS, msg_level)
        self.assertEqual(response.url, reverse("learning_unit", args=[self.learning_unit_year.id]))

        for generated_container_year in self.generate_container:
            learning_component_year = generated_container_year.learning_component_cm_full
            self.check_postponement(learning_component_year)

    def check_postponement(self, learning_component_year):
        learning_component_year.refresh_from_db()
        self.assertEqual(learning_component_year.planned_classes, 1)
        self.assertEqual(learning_component_year.hourly_volume_partial_q1, 0)
        self.assertEqual(learning_component_year.repartition_volume_requirement_entity, 1)
        self.assertEqual(learning_component_year.repartition_volume_additional_entity_1, 0.5)
        self.assertEqual(learning_component_year.repartition_volume_additional_entity_2, 0.5)

    @mock.patch('base.models.program_manager.is_program_manager')
    @mock.patch('base.views.layout.render')
    def test_learning_unit_volumes_management_post_wrong_data(self, mock_render, mock_program_manager):
        mock_program_manager.return_value = True

        request_factory = RequestFactory()
        data = get_valid_formset_data(self.learning_unit_year.acronym)
        data.update(get_valid_formset_data(self.learning_unit_year_partim.acronym))
        data.update({'LDROI1200A-0-volume_total': 3})
        data.update({'LDROI1200A-0-volume_q2': 3})
        data.update({'LDROI1200A-0-volume_requirement_entity': 2})
        data.update({'LDROI1200A-0-volume_total_requirement_entities': 3})

        request = request_factory.post(reverse(learning_unit_volumes_management,
                                               kwargs={
                                                   'learning_unit_year_id': self.learning_unit_year.id,
                                                   'form_type': 'full'
                                               }),
                                       data=data)

        request.user = self.user
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        learning_unit_volumes_management(request, learning_unit_year_id=self.learning_unit_year.id, form_type="full")
        # Volumes of partims can be greater than parent's
        msg_level = [m.level for m in get_messages(request)]
        msg = [m.message for m in get_messages(request)]
        self.assertEqual(len(msg), 1)
        self.assertIn(messages.SUCCESS, msg_level)

    @mock.patch('base.models.program_manager.is_program_manager')
    def test_learning_unit_volumes_management_post_wrong_data_ajax(self, mock_program_manager):
        mock_program_manager.return_value = True

        request_factory = RequestFactory()
        data = get_valid_formset_data(self.learning_unit_year.acronym)
        data.update(get_valid_formset_data(self.learning_unit_year_partim.acronym))
        data.update({'LDROI1200A-0-volume_total': 3})
        data.update({'LDROI1200A-0-volume_q2': 3})
        data.update({'LDROI1200A-0-volume_requirement_entity': 2})
        data.update({'LDROI1200A-0-volume_total_requirement_entities': 3})

        request = request_factory.post(reverse(learning_unit_volumes_management,
                                               kwargs={
                                                   'learning_unit_year_id': self.learning_unit_year.id,
                                                   'form_type': 'full'
                                               }),
                                       data=data,
                                       HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        request.user = self.user

        response = learning_unit_volumes_management(request,
                                                    learning_unit_year_id=self.learning_unit_year.id,
                                                    form_type="full")
        # Volumes of partims can be greater than parent's
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_with_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_when_user_has_not_permission(self):
        a_person = PersonFactory()
        self.client.force_login(a_person.user)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, 'access_denied.html')

    @mock.patch("base.business.learning_units.perms.is_eligible_for_modification", side_effect=lambda luy, pers: False)
    def test_view_decorated_with_can_perform_learning_unit_modification_permission(self, mock_permission):
        response = self.client.post(self.url)

        self.assertTrue(mock_permission.called)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, 'access_denied.html')

    def test_get_learning_units_for_context(self):
        self.assertListEqual(
            _get_learning_units_for_context(self.learning_unit_year, with_family=True),
            [self.learning_unit_year, self.learning_unit_year_partim]
        )

        self.assertListEqual(
            _get_learning_units_for_context(self.learning_unit_year, with_family=False),
            [self.learning_unit_year]
        )


class TestEntityAutocomplete(TestCase):
    def setUp(self):
        self.super_user = SuperUserFactory()
        self.url = reverse("entity_autocomplete")
        today = datetime.date.today()
        self.external_entity_version = EntityVersionFactory(
            entity_type=entity_type.SCHOOL,
            start_date=today.replace(year=1900),
            end_date=None,
            acronym="DRT",
            entity__organization__type=ACADEMIC_PARTNER
        )

    def test_when_param_is_digit_assert_searching_on_code(self):
        # When searching on "code"
        self.client.force_login(user=self.super_user)
        response = self.client.get(
            self.url, data={'q': 'DRT', 'forward': '{"country": "%s"}' % self.external_entity_version.entity.country.id}
        )
        self._assert_result_is_correct(response)

    def test_with_filter_by_section(self):
        self.client.force_login(user=self.super_user)
        response = self.client.get(
            self.url, data={'forward': '{"country": "%s"}' % self.external_entity_version.entity.country.id}
        )
        self._assert_result_is_correct(response)

    def _assert_result_is_correct(self, response):
        results = self._get_list_of_entities_from_response(response)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['text'], str(self.external_entity_version.verbose_title))

    def _get_list_of_entities_from_response(self, response):
        self.assertEqual(response.status_code, 200)
        json_response = str(response.content, encoding='utf8')
        return json.loads(json_response)['results']

    def test_ordering_external_entities(self):
        country = CountryFactory()

        for letter in ['C', 'A', 'B']:
            EntityVersionFactory(
                entity_type=entity_type.SCHOOL,
                start_date=datetime.date.today().replace(year=1900),
                end_date=None,
                title="{} title".format(letter),
                entity__organization__type=ACADEMIC_PARTNER,
                entity__country=country,
            )
        self.client.force_login(user=self.super_user)
        response = self.client.get(
            self.url, data={'forward': '{"country": "%s"}' % country.id}
        )
        results = self._get_list_of_entities_from_response(response)
        self.assertEqual(results[0]['text'], "A title")
        self.assertEqual(results[1]['text'], "B title")
        self.assertEqual(results[2]['text'], "C title")

    def test_ordering_main_entities(self):
        for letter in ['C', 'A', 'B']:
            EntityVersionFactory(
                entity_type=entity_type.FACULTY,
                start_date=datetime.date.today().replace(year=1900),
                end_date=None,
                acronym="{letter}{letter}{letter}".format(letter=letter),
                entity__organization__type=MAIN
            )
        self.client.force_login(user=self.super_user)
        response = self.client.get(
            self.url, data={'forward': '{"country": ""}'}
        )
        results = self._get_list_of_entities_from_response(response)
        # Assert order and assert that acronym is displayed
        self.assertIn('AAA - ', results[0]['text'])
        self.assertIn('BBB - ', results[1]['text'])
        self.assertIn('CCC - ', results[2]['text'])

