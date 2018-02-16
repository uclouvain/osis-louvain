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
from unittest import mock

from django.contrib import messages
from django.contrib.auth.models import Permission
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from django.http import HttpResponseForbidden, HttpResponseNotFound, HttpResponse
from django.test import TestCase, RequestFactory
from django.urls import reverse

from base.models.enums import learning_unit_periodicity, learning_container_year_types, learning_unit_year_subtypes, \
    entity_container_year_link_type, vacant_declaration_type, attribution_procedure, entity_type, organization_type
from base.tests.factories.academic_year import create_current_academic_year, AcademicYearFactory
from base.tests.factories.business.learning_units import LearningUnitsMixin
from base.tests.factories.campus import CampusFactory
from base.tests.factories.entity_container_year import EntityContainerYearFactory
from base.tests.factories.entity_version import EntityVersionFactory
from base.tests.factories.learning_container_year import LearningContainerYearFactory
from base.tests.factories.learning_unit_year import LearningUnitYearFactory
from base.tests.factories.organization import OrganizationFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.person_entity import PersonEntityFactory
from base.tests.factories.proposal_learning_unit import ProposalLearningUnitFactory
from base.tests.factories.user import UserFactory, SuperUserFactory
from base.views.learning_units.edition import learning_unit_edition


class TestLearningUnitEditionView(TestCase, LearningUnitsMixin):

    def setUp(self):
        super().setUp()
        self.user = UserFactory(username="YodaTheJediMaster")
        self.person = PersonFactory(user=self.user)
        self.permission = Permission.objects.get(codename="can_edit_learningunit_date")
        self.person.user.user_permissions.add(self.permission)
        self.client.force_login(self.user)

        self.setup_academic_years()
        self.learning_unit = self.setup_learning_unit(self.current_academic_year.year, learning_unit_periodicity.ANNUAL)
        self.learning_container_year = self.setup_learning_container_year(
            academic_year=self.current_academic_year,
            container_type=learning_container_year_types.COURSE
        )
        self.learning_unit_year = self.setup_learning_unit_year(
            self.current_academic_year,
            self.learning_unit,
            self.learning_container_year,
            learning_unit_periodicity.ANNUAL
        )

        self.a_superuser = SuperUserFactory()
        self.a_superperson = PersonFactory(user=self.a_superuser)

    def test_view_learning_unit_edition_permission_denied(self):
        from base.views.learning_units.edition import learning_unit_edition

        response = self.client.get(reverse(learning_unit_edition, args=[self.learning_unit_year.id]))
        self.assertEqual(response.status_code, 403)

    @mock.patch('base.business.learning_units.perms.is_eligible_for_modification_end_date')
    @mock.patch('base.views.layout.render')
    def test_view_learning_unit_edition_get(self, mock_render, mock_perms):
        mock_perms.return_value = True

        request_factory = RequestFactory()
        request = request_factory.get(reverse('learning_unit_edition', args=[self.learning_unit_year.id]))
        request.user = self.a_superuser

        learning_unit_edition(request, self.learning_unit_year.id)

        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, "learning_unit/edition.html")

    @mock.patch('base.business.learning_units.perms.is_eligible_for_modification_end_date')
    @mock.patch('base.views.layout.render')
    def test_view_learning_unit_edition_post(self, mock_render, mock_perms):
        mock_perms.return_value = True

        request_factory = RequestFactory()

        form_data = {"academic_year": self.current_academic_year.pk}
        request = request_factory.post(reverse('learning_unit_edition', args=[self.learning_unit_year.id]),
                                       data=form_data)
        request.user = self.a_superuser
        setattr(request, 'session', 'session')
        setattr(request, '_messages', FallbackStorage(request))

        learning_unit_edition(request, self.learning_unit_year.id)

        msg_level = [m.level for m in get_messages(request)]
        msg = [m.message for m in get_messages(request)]
        self.assertEqual(len(msg), 1)
        self.assertIn(messages.SUCCESS, msg_level)


class TestEditLearningUnit(TestCase):
    @classmethod
    def setUpTestData(cls):
        an_academic_year = create_current_academic_year()
        learning_container_year = LearningContainerYearFactory(
            academic_year=an_academic_year,
            container_type=learning_container_year_types.COURSE,
            type_declaration_vacant=vacant_declaration_type.DO_NOT_ASSIGN,
            campus=CampusFactory(organization=OrganizationFactory(type=organization_type.MAIN)))
        cls.learning_unit_year = LearningUnitYearFactory(learning_container_year=learning_container_year,
                                                         acronym="LOSIS4512",
                                                         academic_year=an_academic_year,
                                                         subtype=learning_unit_year_subtypes.FULL,
                                                         attribution_procedure=attribution_procedure.INTERNAL_TEAM)

        cls.partim_learning_unit = LearningUnitYearFactory(learning_container_year=learning_container_year,
                                                           acronym="LOSIS4512A",
                                                           academic_year=an_academic_year,
                                                           subtype=learning_unit_year_subtypes.PARTIM)

        cls.requirement_entity_container = EntityContainerYearFactory(
            learning_container_year=learning_container_year, type=entity_container_year_link_type.REQUIREMENT_ENTITY)
        cls.requirement_entity_container.entity.organization.type = organization_type.MAIN
        cls.requirement_entity_container.entity.organization.save()
        cls.requirement_entity = EntityVersionFactory(entity=cls.requirement_entity_container.entity,
                                                      entity_type=entity_type.SCHOOL,
                                                      start_date=an_academic_year.start_date,
                                                      end_date=None)

        cls.allocation_entity_container = EntityContainerYearFactory(
            learning_container_year=learning_container_year, type=entity_container_year_link_type.ALLOCATION_ENTITY)
        cls.allocation_entity = EntityVersionFactory(entity=cls.allocation_entity_container.entity,
                                                     start_date=an_academic_year.start_date,
                                                     end_date=None)

        cls.additional_entity_container_1 = EntityContainerYearFactory(
            learning_container_year=learning_container_year,
            type=entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1)
        cls.additional_entity_1 = EntityVersionFactory(entity=cls.additional_entity_container_1.entity,
                                                       start_date=an_academic_year.start_date,
                                                       end_date=None)

        cls.additional_entity_container_2 = EntityContainerYearFactory(
            learning_container_year=learning_container_year,
            type=entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2)
        cls.additional_entity_2 = EntityVersionFactory(entity=cls.additional_entity_container_2.entity,
                                                       start_date=an_academic_year.start_date,
                                                       end_date=None)

        cls.person = PersonEntityFactory(entity=cls.requirement_entity_container.entity).person
        cls.user = cls.person.user
        cls.user.user_permissions.add(Permission.objects.get(codename="can_edit_learningunit"),
                                      Permission.objects.get(codename="can_access_learningunit"))
        cls.url = reverse("edit_learning_unit", args=[cls.learning_unit_year.id])

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

    def test_cannot_modify_learning_unit_on_modification_proposal(self):
        ProposalLearningUnitFactory(learning_unit_year=self.learning_unit_year)

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_template_used_for_get_request(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "learning_unit/modification.html")
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_context_used_for_get_request(self):
        response = self.client.get(self.url)

        context = response.context
        self.assertEqual(context["learning_unit_year"], self.learning_unit_year)
        self.assertTrue(context["form"])

    def test_form_initial_data(self):
        response = self.client.get(self.url)
        form = response.context["form"]
        initial_data = form.initial
        expected_initial = {
            "acronym": self.learning_unit_year.acronym[1:],
            "academic_year": self.learning_unit_year.academic_year.id,
            "status": self.learning_unit_year.status,
            "credits": self.learning_unit_year.credits,
            "common_title": self.learning_unit_year.learning_container_year.common_title,
            "common_title_english": self.learning_unit_year.learning_container_year.common_title_english,
            "partial_title": self.learning_unit_year.specific_title,
            "partial_english_title": self.learning_unit_year.specific_title_english,
            "session": self.learning_unit_year.session,
            "subtype": self.learning_unit_year.subtype,
            "first_letter": self.learning_unit_year.acronym[0],
            "container_type": self.learning_unit_year.learning_container_year.container_type,
            "faculty_remark": self.learning_unit_year.learning_unit.faculty_remark,
            "other_remark": self.learning_unit_year.learning_unit.other_remark,
            "periodicity": self.learning_unit_year.learning_unit.periodicity,
            "quadrimester": self.learning_unit_year.quadrimester,
            "campus": self.learning_unit_year.learning_container_year.campus.id,
            "requirement_entity": self.requirement_entity.id,
            "allocation_entity": self.allocation_entity.id,
            "additional_requirement_entity_1": self.additional_entity_1.id,
            "additional_requirement_entity_2": self.additional_entity_2.id,
            "language": self.learning_unit_year.learning_container_year.language.id,
            "is_vacant": self.learning_unit_year.learning_container_year.is_vacant,
            "team": self.learning_unit_year.learning_container_year.team,
            "type_declaration_vacant": self.learning_unit_year.learning_container_year.type_declaration_vacant,
            "attribution_procedure": self.learning_unit_year.attribution_procedure
        }
        self.assertDictEqual(initial_data, expected_initial)

    @mock.patch("base.views.learning_units.edition.update_learning_unit_year_with_report", side_effect=None)
    @mock.patch("base.views.learning_units.edition.update_learning_unit_year_entities_with_report", side_effect=None)
    def test_valid_post_request(self, mock_update_learning_unit_year, mock_update_entities):
        form_data = {
            "acronym": self.learning_unit_year.acronym[1:],
            "credits": str(self.learning_unit_year.credits + 1),
            "common_title": self.learning_unit_year.learning_container_year.common_title,
            "first_letter": self.learning_unit_year.acronym[0],
            "periodicity": learning_unit_periodicity.ANNUAL,
            "campus": str(self.learning_unit_year.learning_container_year.campus.id),
            "requirement_entity": str(self.requirement_entity.id),
            "allocation_entity": str(self.requirement_entity.id),
            "language": str(self.learning_unit_year.learning_container_year.language.id)
        }
        response = self.client.post(self.url, data=form_data)

        self.assertTrue(mock_update_learning_unit_year.called)
        self.assertTrue(mock_update_entities.called)

        expected_redirection = reverse("learning_unit", args=[self.learning_unit_year.id])
        self.assertRedirects(response, expected_redirection)
