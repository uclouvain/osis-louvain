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
import json
import urllib
from http import HTTPStatus
from unittest import mock

import bs4
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import Permission, Group
from django.contrib.messages import get_messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, HttpResponseNotFound, HttpResponse, HttpResponseRedirect
from django.test import TestCase, RequestFactory, override_settings
from waffle.testutils import override_flag

from base.business.education_groups.general_information import PublishException
from base.forms.education_group_admission import UpdateTextForm
from base.forms.education_group_pedagogy_edit import EducationGroupPedagogyEditForm
from base.models.admission_condition import AdmissionCondition, AdmissionConditionLine, CONDITION_ADMISSION_ACCESSES
from base.models.enums import education_group_categories, academic_calendar_type
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.admission_condition import AdmissionConditionFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory, EducationGroupYearCommonFactory, \
    TrainingFactory, EducationGroupYearCommonAgregationFactory, EducationGroupYearCommonBachelorFactory, \
    EducationGroupYearCommonSpecializedMasterFactory, EducationGroupYearCommonMasterFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import PersonFactory, PersonWithPermissionsFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.user import UserFactory, SuperUserFactory
from base.views.education_groups.detail import get_appropriate_common_admission_condition
from cms.enums import entity_name
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory, TranslatedTextRandomFactory


@override_settings(URL_TO_PORTAL_UCL="http://portal-url.com", GET_SECTION_PARAM="sectionsParams")
class EducationGroupGeneralInformations(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        EducationGroupYearCommonFactory(academic_year=cls.current_academic_year)
        cls.education_group_parent = TrainingFactory(
            acronym="Parent",
            academic_year=cls.current_academic_year
        )
        cls.education_group_child = TrainingFactory(
            acronym="Child_1",
            academic_year=cls.current_academic_year
        )
        GroupElementYearFactory(parent=cls.education_group_parent, child_branch=cls.education_group_child)

        cls.cms_label_for_child = TranslatedTextFactory(
            text_label=TextLabelFactory(entity=entity_name.OFFER_YEAR),
            reference=cls.education_group_child.id,
        )

        cls.person = PersonWithPermissionsFactory("can_access_education_group")
        cls.url = reverse(
            "education_group_general_informations",
            args=[cls.education_group_parent.pk, cls.education_group_child.pk]
        )

    def setUp(self):
        self.client.force_login(self.person.user)
        self.perm_patcher = mock.patch(
            "base.business.education_groups.perms.GeneralInformationPerms.is_eligible",
            return_value=True
        )
        self.mocked_perm = self.perm_patcher.start()
        self.addCleanup(self.perm_patcher.stop)

    def test_when_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_user_without_permission(self):
        an_other_user = UserFactory()
        self.client.force_login(an_other_user)

        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_with_non_existent_education_group_year(self):
        non_existent_id = self.education_group_child.id + self.education_group_parent.id
        url = reverse("education_group_diplomas", args=[self.education_group_parent.pk, non_existent_id])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "page_not_found.html")
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_with_education_group_year_of_type_group(self):
        group_education_group_year = EducationGroupYearFactory(
            academic_year=self.current_academic_year
        )
        group_education_group_year.education_group_type.category = education_group_categories.GROUP
        group_education_group_year.education_group_type.save()

        url = reverse(
            "education_group_general_informations",
            args=[group_education_group_year.id, group_education_group_year.id]
        )
        response = self.client.get(url)

        self.assertTemplateUsed(response, "education_group/tab_general_informations.html")
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_case_didactic_offer_ensure_show_finalite_common(self):
        education_group_year = EducationGroupYearFactory(
            education_group_type__name=TrainingType.MASTER_MD_120.name,
            academic_year=self.current_academic_year,
        )
        url = reverse("education_group_general_informations",
                      args=[education_group_year.pk, education_group_year.id])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "education_group/tab_general_informations.html")

        context = response.context
        self.assertEqual(context["parent"], education_group_year)
        self.assertEqual(context["education_group_year"], education_group_year)
        sections = context['sections_with_translated_labels']

        self.assertEqual(sections[0].labels[0]['label'], 'intro')
        self.assertEqual(sections[1].labels[0]['label'], 'finalites_didactiques-commun')

    def test_case_common_do_not_have_double_field_prerequisite(self):
        education_group_year = EducationGroupYearCommonFactory(
            academic_year=self.current_academic_year,
        )
        url = reverse("education_group_general_informations",
                      args=[education_group_year.pk, education_group_year.id])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "education_group/tab_general_informations.html")

        context = response.context
        self.assertEqual(context["parent"], education_group_year)
        self.assertEqual(context["education_group_year"], education_group_year)
        sections = context['sections_with_translated_labels']
        prerequis = {
            'label': 'prerequis',
            'type': 'specific',
            'translation':
                'Ce label prerequis n’existe pas',
            'fr-be': None,
            'en': None
        }
        self.assertIn(prerequis, sections[0].labels)
        self.assertEqual(sections[0].labels.count(prerequis), 1)

    def test_case_user_has_link_to_edit_pedagogy(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/tab_general_informations.html")

        soup = bs4.BeautifulSoup(response.content, 'html.parser')
        self.assertGreater(len(soup.select('a.pedagogy-edit-btn')), 0)

    @mock.patch('base.business.education_groups.perms.GeneralInformationPerms.is_eligible', return_value=False)
    def test_user_has_not_link_to_edit_pedagogy(self, mock_is_eligible_to_edit_general_info):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/tab_general_informations.html")

        soup = bs4.BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(len(soup.select('a.pedagogy-edit-btn')), 0)


class EducationGroupPedagogyUpdateViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.training = TrainingFactory(academic_year=cls.current_academic_year)

        cls.text_label = TextLabelFactory(label='dummy-label')
        cls.translated_text_in_french = TranslatedTextRandomFactory(
            reference=str(cls.training.pk),
            entity=entity_name.OFFER_YEAR,
            text_label=cls.text_label,
            language=settings.LANGUAGE_CODE_FR,
        )
        cls.translated_text_in_english = TranslatedTextRandomFactory(
            reference=str(cls.training.pk),
            entity=entity_name.OFFER_YEAR,
            text_label=cls.text_label,
            language=settings.LANGUAGE_CODE_EN,
        )
        cls.person = PersonWithPermissionsFactory(
            "can_access_education_group",
            "change_pedagogyinformation",
            "change_commonpedagogyinformation"
        )
        cls.url = reverse("education_group_pedagogy_edit", args=[cls.training.pk, cls.training.pk])

    def setUp(self):
        self.perm_patcher = mock.patch(
            "base.business.education_groups.perms.GeneralInformationPerms.is_eligible",
            return_value=True
        )
        self.mocked_perm = self.perm_patcher.start()
        self.addCleanup(self.perm_patcher.stop)
        self.client.force_login(self.person.user)

    def test_when_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, "/login/?next={}".format(self.url))

    @mock.patch('base.business.education_groups.perms.GeneralInformationPerms.is_eligible', return_value=False)
    @mock.patch('base.views.education_group.education_group_year_pedagogy_edit_get')
    @mock.patch('base.views.education_group.education_group_year_pedagogy_edit_post')
    def test_get_pedagogy_info_case_user_without_permission(self, mock_edit_post, mock_edit_get, mock_perms):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

        self.assertFalse(mock_edit_post.called)
        self.assertFalse(mock_edit_get.called)

    @mock.patch('base.views.education_group.education_group_year_pedagogy_edit_get',
                side_effect=lambda *args, **kwargs: HttpResponse())
    @mock.patch('base.views.education_group.education_group_year_pedagogy_edit_post')
    def test_get_pedagogy_info_case_user_with_permission(self, mock_edit_post, mock_edit_get):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponse.status_code)

        self.assertFalse(mock_edit_post.called)
        self.assertTrue(mock_edit_get.called)

    @mock.patch('base.views.education_group.render')
    def test_get_pedagogy_info_ensure_context_data(self, mock_render):
        request = RequestFactory().get(self.url, data={'label': self.text_label.label})
        request.user = self.person.user

        from base.views.education_group import education_group_year_pedagogy_edit_get
        education_group_year_pedagogy_edit_get(request, self.training.pk)

        request, template, context = mock_render.call_args[0]
        self.assertEqual(context['education_group_year'], self.training)
        self.assertEqual(context['label'], self.text_label.label)

        form = context['form']
        self.assertIsInstance(form, EducationGroupPedagogyEditForm)
        self.assertEqual(form.initial['label'], self.text_label.label)
        self.assertEqual(form.initial['text_french'], self.translated_text_in_french.text)
        self.assertEqual(form.initial['text_english'], self.translated_text_in_english.text)

    @mock.patch('base.business.education_groups.perms.GeneralInformationPerms.is_eligible', return_value=False)
    @mock.patch('base.views.education_group.education_group_year_pedagogy_edit_get')
    @mock.patch('base.views.education_group.education_group_year_pedagogy_edit_post')
    def test_post_pedagogy_info_case_user_without_permission(self, mock_edit_post, mock_edit_get, mock_perms):
        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

        self.assertFalse(mock_edit_post.called)
        self.assertFalse(mock_edit_get.called)

    @mock.patch('base.views.education_group.education_group_year_pedagogy_edit_get')
    @mock.patch('base.views.education_group.education_group_year_pedagogy_edit_post',
                side_effect=lambda *args, **kwargs: HttpResponse())
    def test_post_pedagogy_info_case_user_with_permission(self, mock_edit_post, mock_edit_get):
        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, HttpResponse.status_code)

        self.assertTrue(mock_edit_post.called)
        self.assertFalse(mock_edit_get.called)

    def test_education_group_year_pedagogy_edit_post(self):
        post_data = {'label': 'welcome_introduction', 'text_french': 'Salut', 'text_english': 'Hello'}
        request = RequestFactory().post(self.url, data=post_data)

        from base.views.education_group import education_group_year_pedagogy_edit_post
        response = education_group_year_pedagogy_edit_post(request, self.training.pk, self.training.pk)

        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)
        anchor_expected = '#section_welcome_introduction'
        self.assertTrue(anchor_expected in response.url)


class EducationGroupPublishViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = create_current_academic_year()
        cls.training = TrainingFactory(academic_year=cls.academic_year)
        cls.url = reverse('education_group_publish', args=(cls.training.pk, cls.training.pk))
        cls.person = PersonWithPermissionsFactory('can_access_education_group')

    def setUp(self):
        self.client.force_login(self.person.user)

    def test_publish_case_user_not_logged(self):
        self.client.logout()
        response = self.client.post(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_public_case_methods_not_allowed(self):
        methods_not_allowed = ['get', 'delete', 'put']
        for method in methods_not_allowed:
            request_to_call = getattr(self.client, method)
            response = request_to_call(self.url)
            self.assertEqual(response.status_code, 405)

    @mock.patch("base.business.education_groups.general_information.publish", side_effect=lambda e: "portal-url")
    def test_publish_case_ok_redirection_with_success_message(self, mock_publish):
        response = self.client.post(self.url)

        msg = [m.message for m in get_messages(response.wsgi_request)]
        msg_level = [m.level for m in get_messages(response.wsgi_request)]

        self.assertEqual(len(msg), 1)
        self.assertIn(messages.SUCCESS, msg_level)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    @mock.patch("base.business.education_groups.general_information.publish", side_effect=PublishException('error'))
    def test_publish_case_ko_redirection_with_error_message(self, mock_publish):
        response = self.client.post(self.url)

        msg = [m.message for m in get_messages(response.wsgi_request)]
        msg_level = [m.level for m in get_messages(response.wsgi_request)]

        self.assertEqual(len(msg), 1)
        self.assertIn(messages.ERROR, msg_level)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)


@override_flag('education_group_update', active=True)
class EducationGroupViewTestCase(TestCase):
    def setUp(self):
        today = datetime.date.today()
        self.academic_year = AcademicYearFactory(start_date=today,
                                                 end_date=today.replace(year=today.year + 1),
                                                 year=today.year)

        self.type_training = EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        self.type_minitraining = EducationGroupTypeFactory(category=education_group_categories.MINI_TRAINING)
        self.type_group = EducationGroupTypeFactory(category=education_group_categories.GROUP)

    def test_education_administrative_data(self):
        an_education_group = EducationGroupYearFactory()
        self.initialize_session()
        url = reverse("education_group_administrative", args=[an_education_group.id, an_education_group.id])
        response = self.client.get(url)
        self.assertTemplateUsed(response, "education_group/tab_administrative_data.html")
        self.assertEqual(response.context['education_group_year'], an_education_group)
        self.assertEqual(response.context['parent'], an_education_group)

    def test_education_administrative_data_with_root_set(self):
        a_group_element_year = GroupElementYearFactory()
        self.initialize_session()
        url = reverse("education_group_administrative",
                      args=[a_group_element_year.parent.id, a_group_element_year.child_branch.id])
        response = self.client.get(url)
        self.assertTemplateUsed(response, "education_group/tab_administrative_data.html")
        self.assertEqual(response.context['education_group_year'], a_group_element_year.child_branch)
        self.assertEqual(response.context['parent'], a_group_element_year.parent)

    def test_get_sessions_dates(self):
        from base.views.education_groups.detail import get_sessions_dates
        from base.tests.factories.session_exam_calendar import SessionExamCalendarFactory
        from base.tests.factories.academic_calendar import AcademicCalendarFactory
        from base.tests.factories.education_group_year import EducationGroupYearFactory
        from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory

        sessions_quantity = 3
        an_academic_year = AcademicYearFactory()
        academic_calendars = [
            AcademicCalendarFactory(academic_year=an_academic_year,
                                    reference=academic_calendar_type.DELIBERATION)
            for _ in range(sessions_quantity)
        ]
        education_group_year = EducationGroupYearFactory(academic_year=an_academic_year)

        for session, academic_calendar in enumerate(academic_calendars):
            SessionExamCalendarFactory(number_session=session + 1, academic_calendar=academic_calendar)

        offer_year_calendars = [OfferYearCalendarFactory(
            academic_calendar=academic_calendar,
            education_group_year=education_group_year)
            for academic_calendar in academic_calendars]

        self.assertEqual(
            get_sessions_dates(academic_calendars[0].reference, education_group_year),
            {
                'session{}'.format(s + 1): offer_year_calendar
                for s, offer_year_calendar in enumerate(offer_year_calendars)
            }
        )

    @mock.patch('base.business.education_group.can_user_edit_administrative_data')
    def test_education_edit_administrative_data(self, mock_can_user_edit_administrative_data):
        from base.views.education_group import education_group_edit_administrative_data
        self.client.force_login(SuperUserFactory())

        education_group_year = EducationGroupYearFactory(academic_year=self.academic_year)
        mock_can_user_edit_administrative_data.return_value = True

        response = self.client.get(reverse(education_group_edit_administrative_data, kwargs={
            'root_id': education_group_year.id,
            'education_group_year_id': education_group_year.id
        }))

        self.assertTemplateUsed(response, 'education_group/tab_edit_administrative_data.html')
        self.assertEqual(response.context['education_group_year'], education_group_year)
        self.assertEqual(response.context['course_enrollment_validity'], False)
        self.assertEqual(response.context['formset_session_validity'], False)
        self.assertIn('additional_info_form', response.context)

    def test_education_content(self):
        an_education_group = EducationGroupYearFactory()
        self.initialize_session()
        url = reverse("education_group_diplomas", args=[an_education_group.id, an_education_group.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "education_group/tab_diplomas.html")

    def initialize_session(self):
        person = PersonFactory()
        person.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        self.client.force_login(person.user)


class EducationGroupAdministrativedata(TestCase):
    def setUp(self):
        self.person = PersonFactory()

        self.permission_access = Permission.objects.get(codename='can_access_education_group')
        self.person.user.user_permissions.add(self.permission_access)

        self.permission_edit = Permission.objects.get(codename='can_edit_education_group_administrative_data')
        self.person.user.user_permissions.add(self.permission_edit)

        self.education_group_year = EducationGroupYearFactory()
        self.program_manager = ProgramManagerFactory(person=self.person,
                                                     education_group=self.education_group_year.education_group)

        self.url = reverse('education_group_administrative', args=[
            self.education_group_year.id, self.education_group_year.id
        ])
        self.client.force_login(self.person.user)
        create_current_academic_year()

    def test_when_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_user_has_not_permission(self):
        Group.objects.get(name="program_managers").permissions.remove(self.permission_access)
        self.person.user.user_permissions.remove(self.permission_access)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_user_is_not_program_manager_of_education_group(self):
        self.program_manager.delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/tab_administrative_data.html")

        self.assertFalse(response.context["can_edit_administrative_data"])

    def test_user_has_no_permission_to_edit_administrative_data(self):
        self.person.user.user_permissions.remove(self.permission_edit)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/tab_administrative_data.html")

        self.assertFalse(response.context["can_edit_administrative_data"])

    def test_education_group_non_existent(self):
        self.education_group_year.delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTemplateUsed(response, "page_not_found.html")

    def test_with_education_group_year_of_type_mini_training(self):
        mini_training_education_group_year = EducationGroupYearFactory()
        mini_training_education_group_year.education_group_type.category = education_group_categories.MINI_TRAINING
        mini_training_education_group_year.education_group_type.save()

        url = reverse("education_group_administrative",
                      args=[mini_training_education_group_year.id, mini_training_education_group_year.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_with_education_group_year_of_type_group(self):
        group_education_group_year = EducationGroupYearFactory()
        group_education_group_year.education_group_type.category = education_group_categories.GROUP
        group_education_group_year.education_group_type.save()

        url = reverse("education_group_administrative",
                      args=[group_education_group_year.id, group_education_group_year.id])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_user_can_edit_administrative_data(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/tab_administrative_data.html")

        self.assertTrue(response.context["can_edit_administrative_data"])


@override_flag('education_group_update', active=True)
class EducationGroupEditAdministrativeData(TestCase):
    def setUp(self):
        self.person = PersonFactory()

        self.permission = Permission.objects.get(codename='can_edit_education_group_administrative_data')
        self.person.user.user_permissions.add(self.permission)

        self.education_group_year = EducationGroupYearFactory()
        self.program_manager = ProgramManagerFactory(person=self.person,
                                                     education_group=self.education_group_year.education_group)
        self.url = reverse('education_group_edit_administrative',
                           args=[self.education_group_year.id, self.education_group_year.id])
        self.client.force_login(self.person.user)

    def test_when_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_user_has_not_permission(self):
        self.person.user.user_permissions.remove(self.permission)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_user_is_not_program_manager_of_education_group(self):
        self.program_manager.delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
        self.assertTemplateUsed(response, "access_denied.html")

    def test_education_group_non_existent(self):
        self.education_group_year.delete()
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)
        self.assertTemplateUsed(response, "page_not_found.html")

    def test_with_education_group_year_of_type_mini_training(self):
        mini_training_education_group_year = EducationGroupYearFactory()
        mini_training_education_group_year.education_group_type.category = education_group_categories.MINI_TRAINING
        mini_training_education_group_year.education_group_type.save()

        url = reverse("education_group_edit_administrative",
                      args=[mini_training_education_group_year.id, mini_training_education_group_year.id])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_with_education_group_year_of_type_group(self):
        group_education_group_year = EducationGroupYearFactory()
        group_education_group_year.education_group_type.category = education_group_categories.GROUP
        group_education_group_year.education_group_type.save()

        url = reverse("education_group_edit_administrative",
                      args=[group_education_group_year.id, group_education_group_year.id])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)


class AdmissionConditionEducationGroupYearTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory()
        cls.education_group_parent = TrainingFactory(acronym="Parent", academic_year=cls.academic_year)
        cls.education_group_child = TrainingFactory(acronym="Child_1", academic_year=cls.academic_year)

        cls.agregation_adm_cond = AdmissionConditionFactory(
            education_group_year=EducationGroupYearCommonAgregationFactory(academic_year=cls.academic_year)
        )
        cls.bachelor_adm_cond = AdmissionConditionFactory(
            education_group_year=EducationGroupYearCommonBachelorFactory(academic_year=cls.academic_year)
        )
        cls.special_master_adm_cond = AdmissionConditionFactory(
            education_group_year=EducationGroupYearCommonSpecializedMasterFactory(academic_year=cls.academic_year)
        )
        cls.master_adm_cond = AdmissionConditionFactory(
            education_group_year=EducationGroupYearCommonMasterFactory(academic_year=cls.academic_year)
        )
        GroupElementYearFactory(parent=cls.education_group_parent, child_branch=cls.education_group_child)

        cls.cms_label_for_child = TranslatedTextFactory(
            text_label__entity=entity_name.OFFER_YEAR,
            reference=cls.education_group_child.id
        )

        cls.person = PersonWithPermissionsFactory(
            "can_access_education_group",
            "change_admissioncondition",
            "change_commonadmissioncondition",
        )
        cls.url = reverse(
            "education_group_year_admission_condition_edit",
            args=[cls.education_group_parent.pk, cls.education_group_child.pk]
        )

    def setUp(self):
        self.perm_patcher = mock.patch(
            "base.business.education_groups.perms.AdmissionConditionPerms.is_eligible",
            return_value=True
        )
        self.mocked_perm = self.perm_patcher.start()
        self.addCleanup(self.perm_patcher.stop)
        self.client.force_login(self.person.user)

    def test_when_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)

        self.assertRedirects(response, "/login/?next={}".format(self.url))

    def test_user_without_permission(self):
        an_other_user = UserFactory()
        self.client.force_login(an_other_user)

        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_user_has_link_to_edit_conditions(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/tab_admission_conditions.html")

        soup = bs4.BeautifulSoup(response.content, 'html.parser')
        self.assertGreater(len(soup.select('button.btn-publish')), 0)

    @mock.patch('base.business.education_groups.perms.AdmissionConditionPerms.is_eligible', return_value=False)
    def test_user_has_not_link_to_edit_conditions(self, mock_perms):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/tab_admission_conditions.html")

        soup = bs4.BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(len(soup.select('button.btn-publish')), 0)

    def test_case_free_text_is_not_show_when_common(self):
        AcademicYearFactory(current=True)
        common_bachelor = EducationGroupYearCommonBachelorFactory()
        url_edit_common = reverse(
            "education_group_year_admission_condition_edit",
            args=[common_bachelor.pk, common_bachelor.pk]
        )

        response = self.client.get(url_edit_common)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/tab_admission_conditions.html")

        self.assertFalse(response.context['info']['show_free_text'])

    def test_case_admission_condition_remove_line_not_found(self):
        delete_url = reverse(
            "education_group_year_admission_condition_remove_line",
            args=[self.education_group_parent.pk, self.education_group_child.pk]
        )
        response = self.client.get(delete_url, data={'id': 0})

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_case_admission_condition_remove_line(self):
        delete_url = reverse(
            "education_group_year_admission_condition_remove_line",
            args=[self.education_group_parent.pk, self.education_group_child.pk]
        )

        admission_condition = AdmissionCondition.objects.create(education_group_year=self.education_group_child)
        admission_condition_line = AdmissionConditionLine.objects.create(admission_condition=admission_condition)
        qs = AdmissionConditionLine.objects.filter(admission_condition=admission_condition)

        self.assertEqual(qs.count(), 1)
        response = self.client.get(delete_url, data={'id': admission_condition_line.pk})
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)
        self.assertEqual(qs.count(), 0)

    @mock.patch('base.views.education_group.education_group_year_admission_condition_update_line_get',
                side_effect=lambda *args, **kwargs: HttpResponse())
    @mock.patch('base.views.education_group.education_group_year_admission_condition_update_line_post')
    def test_case_admission_condition_update_line(self, mock_edit_post, mock_edit_get):
        update_url = reverse(
            "education_group_year_admission_condition_update_line",
            args=[self.education_group_parent.pk, self.education_group_child.pk]
        )
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, HttpResponse.status_code)

        self.assertFalse(mock_edit_post.called)
        self.assertTrue(mock_edit_get.called)

    @mock.patch('base.views.education_group.get_content_of_admission_condition_line')
    @mock.patch('base.views.education_group.render')
    def test_case_admission_condition_update_existing_line(self, mock_render, mock_get_content):
        section = 'ucl_bachelors'
        admission_condition = AdmissionCondition.objects.create(education_group_year=self.education_group_child)
        admission_condition_line = AdmissionConditionLine.objects.create(admission_condition=admission_condition,
                                                                         section=section)

        mock_get_content.return_value = {
            'message': 'read',
            'section': section,
            'id': admission_condition_line.id,
            'diploma': 'Diploma',
            'conditions': 'Conditions',
            'access': CONDITION_ADMISSION_ACCESSES[2][0],
            'remarks': 'Remarks'
        }

        info = {
            'section': section,
            'language': 'fr-be',
            'id': admission_condition_line.id,
        }
        request = RequestFactory().get('/?{}'.format(urllib.parse.urlencode(info)))

        from base.views.education_group import education_group_year_admission_condition_update_line_get
        response = education_group_year_admission_condition_update_line_get(request)

        mock_get_content.assert_called_once_with('read', admission_condition_line, '')

    @mock.patch('base.views.education_group.get_content_of_admission_condition_line')
    @mock.patch('base.views.education_group.render')
    def test_education_group_year_admission_condition_update_line_get_no_admission_condition_line(self,
                                                                                                  mock_render,
                                                                                                  mock_get_content):
        info = {
            'section': 'ucl_bachelors',
            'language': 'fr',
        }
        request = RequestFactory().get('/?section={section}&language={language}'.format(**info))

        from base.views.education_group import education_group_year_admission_condition_update_line_get
        response = education_group_year_admission_condition_update_line_get(request)

        mock_get_content.not_called()

    def test_save_form_to_admission_condition_line_creation_mode_true(self):
        from base.views.education_group import save_form_to_admission_condition_line
        admission_condition = AdmissionCondition.objects.create(education_group_year=self.education_group_child)
        form = mock.Mock(cleaned_data={
            'language': 'fr',
            'section': 'ucl_bachelors',
            'admission_condition_line': '',
            'diploma': 'Diploma',
            'conditions': 'Conditions',
            'remarks': 'Remarks',
            'access': CONDITION_ADMISSION_ACCESSES[2][0],
        })

        request = RequestFactory().get('/')

        queryset = AdmissionConditionLine.objects.filter(admission_condition=admission_condition)
        self.assertEqual(queryset.count(), 0)

        save_form_to_admission_condition_line(self.education_group_child.id, creation_mode=True, form=form)

        self.assertEqual(queryset.count(), 1)

    def test_save_form_to_admission_condition_line_creation_mode_false(self):
        from base.views.education_group import save_form_to_admission_condition_line
        admission_condition = AdmissionCondition.objects.create(education_group_year=self.education_group_child)
        admission_condition_line = AdmissionConditionLine.objects.create(admission_condition=admission_condition)
        form = mock.Mock(cleaned_data={
            'language': 'fr',
            'section': 'ucl_bachelors',
            'admission_condition_line': admission_condition_line.id,
            'diploma': 'Diploma',
            'conditions': 'Conditions',
            'remarks': 'Remarks',
            'access': CONDITION_ADMISSION_ACCESSES[2][0],
        })

        queryset = AdmissionConditionLine.objects.filter(admission_condition=admission_condition)
        self.assertEqual(queryset.count(), 1)

        save_form_to_admission_condition_line(self.education_group_child.id, creation_mode=False, form=form)

        self.assertEqual(queryset.count(), 1)

    @mock.patch('base.views.education_group.save_form_to_admission_condition_line')
    def test_education_group_year_admission_condition_update_line_post_bad_form(self, mock_save_form):
        from base.views.education_group import education_group_year_admission_condition_update_line_post
        form = {
            'admission_condition_line': '',
        }
        request = RequestFactory().post('/', form)
        response = education_group_year_admission_condition_update_line_post(request,
                                                                             self.education_group_parent.id,
                                                                             self.education_group_child.id)
        # the form is not called because this one is not valid
        mock_save_form.not_called()
        # we can not test the redirection because we don't have a client with the returned response.
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    @mock.patch('base.views.education_group.save_form_to_admission_condition_line')
    def test_education_group_year_admission_condition_update_line_post_creation_mode(self, mock_save_form):
        from base.views.education_group import education_group_year_admission_condition_update_line_post
        form = {
            'admission_condition_line': '',
            'language': 'fr',
            'section': 'ucl_bachelors',
            'diploma': 'Diploma',
            'conditions': 'Conditions',
            'remarks': 'Remarks',
            'access': CONDITION_ADMISSION_ACCESSES[2][0],
        }
        request = RequestFactory().post('/', form)
        response = education_group_year_admission_condition_update_line_post(request,
                                                                             self.education_group_parent.id,
                                                                             self.education_group_child.id)

        education_group_id, creation_mode, unused = mock_save_form.call_args[0]
        self.assertEqual(education_group_id, self.education_group_child.id)
        self.assertEqual(creation_mode, True)
        # we can not test the redirection because we don't have a client with the returned response.
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    @mock.patch('base.views.education_group.save_form_to_admission_condition_line')
    def test_education_group_year_admission_condition_update_line_post_creation_mode_off(self, mock_save_form):
        from base.views.education_group import education_group_year_admission_condition_update_line_post
        admission_condition = AdmissionCondition.objects.create(education_group_year=self.education_group_child)
        admission_condition_line = AdmissionConditionLine.objects.create(admission_condition=admission_condition)
        form = {
            'admission_condition_line': admission_condition_line.id,
            'language': 'fr',
            'section': 'ucl_bachelors',
            'diploma': 'Diploma',
            'conditions': 'Conditions',
            'remarks': 'Remarks',
            'access': CONDITION_ADMISSION_ACCESSES[2][0]
        }
        request = RequestFactory().post('/', form)
        result = education_group_year_admission_condition_update_line_post(request,
                                                                           self.education_group_parent.id,
                                                                           self.education_group_child.id)

        education_group_id, creation_mode, unused = mock_save_form.call_args[0]
        self.assertEqual(education_group_id, self.education_group_child.id)
        self.assertEqual(creation_mode, False)

    def test_get_content_of_admission_condition_line(self):
        from base.views.education_group import get_content_of_admission_condition_line

        admission_condition_line = mock.Mock(diploma='diploma',
                                             conditions='conditions',
                                             access=CONDITION_ADMISSION_ACCESSES[2][0],
                                             remarks='remarks')

        response = get_content_of_admission_condition_line('updated', admission_condition_line, '')
        self.assertEqual(response['message'], 'updated')
        self.assertEqual(response['diploma'], 'diploma')
        self.assertEqual(response['access'], CONDITION_ADMISSION_ACCESSES[2][0])

    @mock.patch('base.business.education_groups.perms.AdmissionConditionPerms.is_eligible', return_value=False)
    @mock.patch('base.views.education_group.education_group_year_admission_condition_update_text_post')
    @mock.patch('base.views.education_group.education_group_year_admission_condition_update_text_get')
    def test_case_update_text_admission_condition_without_perms(self, mock_update_get, mock_update_post, mock_perms):
        update_url = reverse(
            "education_group_year_admission_condition_update_text",
            args=[self.education_group_parent.pk, self.education_group_child.pk]
        )
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

        self.assertFalse(mock_update_post.called)
        self.assertFalse(mock_update_get.called)

    @mock.patch('base.views.education_group.education_group_year_admission_condition_update_text_post')
    @mock.patch('base.views.education_group.education_group_year_admission_condition_update_text_get',
                side_effect=lambda *args, **kwargs: HttpResponse())
    def test_case_get_update_text_admission_condition(self, mock_update_get, mock_update_post):
        update_url = reverse(
            "education_group_year_admission_condition_update_text",
            args=[self.education_group_parent.pk, self.education_group_child.pk]
        )
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, HttpResponse.status_code)

        self.assertFalse(mock_update_post.called)
        self.assertTrue(mock_update_get.called)

    @mock.patch('base.views.education_group.education_group_year_admission_condition_update_text_post',
                side_effect=lambda *args, **kwargs: HttpResponse())
    @mock.patch('base.views.education_group.education_group_year_admission_condition_update_text_get')
    def test_case_post_update_text_admission_condition(self, mock_update_get, mock_update_post):
        update_url = reverse(
            "education_group_year_admission_condition_update_text",
            args=[self.education_group_parent.pk, self.education_group_child.pk]
        )
        response = self.client.post(update_url)
        self.assertEqual(response.status_code, HttpResponse.status_code)

        self.assertTrue(mock_update_post.called)
        self.assertFalse(mock_update_get.called)

    @mock.patch('base.views.education_group.render')
    def test_get_update_text_admission_condition_ensure_context_data(self, mock_render):
        AdmissionCondition.objects.create(
            education_group_year=self.education_group_child,
            text_free='texte en français',
            text_free_en='text in english'
        )

        update_url = reverse(
            "education_group_year_admission_condition_update_text",
            args=[self.education_group_parent.pk, self.education_group_child.pk]
        )
        querystring_data = {'section': 'free', 'language': 'fr', 'title': 'Free Text'}
        request = RequestFactory().get(update_url, data=querystring_data)
        request.user = self.person.user

        from base.views.education_group import education_group_year_admission_condition_update_text_get
        education_group_year_admission_condition_update_text_get(request, self.education_group_child.id)

        unused_request, template_name, context = mock_render.call_args[0]

        self.assertEqual(template_name, 'education_group/condition_text_edit.html')
        self.assertIn('form', context)

        form = context['form']
        self.assertIsInstance(form, UpdateTextForm)
        self.assertEqual(form.initial['section'], querystring_data['section'])
        self.assertEqual(form.initial['text_fr'], self.education_group_child.admissioncondition.text_free)
        self.assertEqual(form.initial['text_en'], self.education_group_child.admissioncondition.text_free_en)

    def test_education_group_year_admission_condition_update_text_post_form_is_valid(self):
        AdmissionCondition.objects.create(education_group_year=self.education_group_child)

        update_url = reverse(
            "education_group_year_admission_condition_update_text",
            args=[self.education_group_parent.pk, self.education_group_child.pk]
        )
        post_data = {'section': 'free', 'text_fr': 'Texte en Français', 'text_en': 'Text in English'}
        request = RequestFactory().post(update_url, data=post_data)
        request.user = self.person.user

        from base.views.education_group import education_group_year_admission_condition_update_text_post
        response = education_group_year_admission_condition_update_text_post(
            request,
            self.education_group_parent.id,
            self.education_group_child.id,
        )

        self.education_group_child.admissioncondition.refresh_from_db()
        self.assertEqual(self.education_group_child.admissioncondition.text_free, post_data['text_fr'])
        self.assertEqual(self.education_group_child.admissioncondition.text_free_en, post_data['text_en'])
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    @mock.patch('base.forms.education_group_admission.UpdateTextForm.is_valid', return_value=False)
    def test_education_group_year_admission_condition_update_text_post_form_is_not_valid(self, mock_is_valid):
        update_url = reverse(
            "education_group_year_admission_condition_update_text",
            args=[self.education_group_parent.pk, self.education_group_child.pk]
        )
        request = RequestFactory().post(update_url, data={})

        from base.views.education_group import education_group_year_admission_condition_update_text_post
        response = education_group_year_admission_condition_update_text_post(
            request,
            self.education_group_parent.id,
            self.education_group_child.id,
        )

        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    def test_webservice_education_group_year_admission_condition_line_order(self):
        kwargs = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

        admission_condition = AdmissionCondition.objects.create(education_group_year=self.education_group_child)

        admission_condition_line_1 = AdmissionConditionLine.objects.create(admission_condition=admission_condition)
        admission_condition_line_2 = AdmissionConditionLine.objects.create(admission_condition=admission_condition)

        self.assertLess(admission_condition_line_1.order, admission_condition_line_2.order)

        url = reverse('education_group_year_admission_condition_line_order', kwargs={
            'root_id': self.education_group_parent.id,
            'education_group_year_id': self.education_group_child.id,
        })

        data = {
            'action': 'down',
            'record': admission_condition_line_1.id,
        }

        response = self.client.post(url, data=json.dumps(data), content_type='application/json', **kwargs)

        self.assertEqual(response.status_code, HttpResponse.status_code)

        admission_condition_line_1.refresh_from_db()
        admission_condition_line_2.refresh_from_db()

        self.assertGreater(admission_condition_line_1.order, admission_condition_line_2.order)

        data = {
            'action': 'up',
            'record': admission_condition_line_1.id,
        }

        response = self.client.post(url, data=json.dumps(data), content_type='application/json', **kwargs)

        self.assertEqual(response.status_code, HttpResponse.status_code)

        admission_condition_line_1.refresh_from_db()
        admission_condition_line_2.refresh_from_db()

        self.assertLess(admission_condition_line_1.order, admission_condition_line_2.order)

    def test_education_group_year_admission_condition_change_lang_tab(self):
        url = reverse('tab_lang_edit', args=[self.education_group_parent.pk, self.education_group_child.pk, 'fr'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)

    def test_get_appropriate_common_offer_for_common(self):
        edy = EducationGroupYearCommonFactory(
            education_group_type__minitraining=True,
            academic_year=self.academic_year
        )
        result = get_appropriate_common_admission_condition(edy)
        self.assertEqual(result, None)

    def test_get_appropriate_common_offer_for_bachelor(self):
        edy = EducationGroupYearFactory(
            education_group_type__name=TrainingType.BACHELOR.name,
            academic_year=self.academic_year
        )
        result = get_appropriate_common_admission_condition(edy)
        self.assertEqual(result, self.bachelor_adm_cond)

    def test_get_appropriate_common_offer_for_agregation(self):
        edy = EducationGroupYearFactory(
            education_group_type__name=TrainingType.AGGREGATION.name,
            academic_year=self.academic_year
        )
        result = get_appropriate_common_admission_condition(edy)
        self.assertEqual(result, self.agregation_adm_cond)

    def test_get_appropriate_common_offer_for_master(self):
        edy = EducationGroupYearFactory(
            education_group_type__name=TrainingType.PGRM_MASTER_120.name,
            academic_year=self.academic_year
        )
        result = get_appropriate_common_admission_condition(edy)
        self.assertEqual(result, self.master_adm_cond)

        edy = EducationGroupYearFactory(
            education_group_type__name=TrainingType.MASTER_M1.name,
            academic_year=self.academic_year
        )
        result = get_appropriate_common_admission_condition(edy)
        self.assertEqual(result, self.master_adm_cond)

    def test_get_appropriate_common_offer_for_special_master(self):
        edy = EducationGroupYearFactory(
            education_group_type__name=TrainingType.MASTER_MC.name,
            academic_year=self.academic_year
        )
        result = get_appropriate_common_admission_condition(edy)
        self.assertEqual(result, self.special_master_adm_cond)
