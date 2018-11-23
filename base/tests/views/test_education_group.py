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
import reversion
from django.contrib import messages
from django.contrib.auth.models import Permission, Group
from django.contrib.messages import get_messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, HttpResponseNotFound, HttpResponse
from django.test import TestCase, RequestFactory
from waffle.testutils import override_flag

from base.models.admission_condition import AdmissionCondition, AdmissionConditionLine, CONDITION_ADMISSION_ACCESSES
from base.models.enums import education_group_categories, academic_calendar_type
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.certificate_aim import CertificateAimFactory
from base.tests.factories.education_group_certificate_aim import EducationGroupCertificateAimFactory
from base.tests.factories.education_group_language import EducationGroupLanguageFactory
from base.tests.factories.education_group_organization import EducationGroupOrganizationFactory
from base.tests.factories.education_group_type import EducationGroupTypeFactory
from base.tests.factories.education_group_year import EducationGroupYearFactory
from base.tests.factories.group_element_year import GroupElementYearFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.user import UserFactory
from cms.enums import entity_name
from cms.tests.factories.text_label import TextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextFactory, TranslatedTextRandomFactory


class EducationGroupRead(TestCase):
    @classmethod
    def setUpTestData(cls):
        today = datetime.date.today()
        academic_year = AcademicYearFactory(start_date=today, end_date=today.replace(year=today.year + 1),
                                            year=today.year)
        cls.education_group_parent = EducationGroupYearFactory(acronym="Parent", academic_year=academic_year)
        cls.education_group_child_1 = EducationGroupYearFactory(acronym="Child_1", academic_year=academic_year)
        cls.education_group_child_2 = EducationGroupYearFactory(acronym="Child_2", academic_year=academic_year)

        GroupElementYearFactory(parent=cls.education_group_parent, child_branch=cls.education_group_child_1)
        GroupElementYearFactory(parent=cls.education_group_parent, child_branch=cls.education_group_child_2)

        cls.education_group_language_parent = \
            EducationGroupLanguageFactory(education_group_year=cls.education_group_parent)
        cls.education_group_language_child_1 = \
            EducationGroupLanguageFactory(education_group_year=cls.education_group_child_1)

        cls.user = PersonFactory().user
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        cls.url = reverse("education_group_read",
                          args=[cls.education_group_parent.id, cls.education_group_child_1.id])

    def setUp(self):
        self.client.force_login(self.user)

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
        non_existent_id = self.education_group_child_1.id + self.education_group_child_2.id + \
                          self.education_group_parent.id
        url = reverse("education_group_read", args=[self.education_group_parent.pk, non_existent_id])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "page_not_found.html")
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_without_get_data(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "education_group/tab_identification.html")

        context = response.context
        self.assertEqual(context["education_group_year"], self.education_group_child_1)
        self.assertListEqual(context["education_group_languages"],
                             [self.education_group_language_child_1.language.name])
        self.assertEqual(context["enums"], education_group_categories)
        self.assertEqual(context["parent"], self.education_group_parent)

    def test_with_root_set(self):
        response = self.client.get(self.url, data={"root": self.education_group_parent.id})

        self.assertTemplateUsed(response, "education_group/tab_identification.html")

        context = response.context
        self.assertEqual(context["education_group_year"], self.education_group_child_1)
        self.assertListEqual(context["education_group_languages"],
                             [self.education_group_language_child_1.language.name])
        self.assertEqual(context["enums"], education_group_categories)
        self.assertEqual(context["parent"], self.education_group_parent)

    def test_with_non_existent_root_id(self):
        non_existent_id = self.education_group_child_1.id + self.education_group_child_2.id + \
                          self.education_group_parent.id
        url = reverse("education_group_read",
                      args=[non_existent_id, self.education_group_child_1.id])

        response = self.client.get(url)

        self.assertTemplateUsed(response, "page_not_found.html")
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_with_root_set_as_current_education_group_year(self):
        response = self.client.get(self.url, data={"root": self.education_group_child_1.id})

        self.assertTemplateUsed(response, "education_group/tab_identification.html")

        context = response.context
        self.assertEqual(context["education_group_year"], self.education_group_child_1)
        self.assertListEqual(context["education_group_languages"],
                             [self.education_group_language_child_1.language.name])
        self.assertEqual(context["enums"], education_group_categories)
        self.assertEqual(context["parent"], self.education_group_parent)

    def test_with_without_education_group_language(self):
        url = reverse("education_group_read", args=[self.education_group_parent.pk, self.education_group_child_2.id])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "education_group/tab_identification.html")

        context = response.context
        self.assertEqual(context["education_group_year"], self.education_group_child_2)
        self.assertListEqual(context["education_group_languages"], [])
        self.assertEqual(context["enums"], education_group_categories)
        self.assertEqual(context["parent"], self.education_group_parent)

    def test_versions(self):
        response = self.client.get(self.url)
        self.assertEqual(len(response.context["versions"]), 0)

        with reversion.create_revision():
            self.education_group_child_1.acronym = "Snape"
            self.education_group_child_1.save()

        response = self.client.get(self.url)
        self.assertEqual(len(response.context["versions"]), 1)

        with reversion.create_revision():
            EducationGroupOrganizationFactory(education_group_year=self.education_group_child_1)

        response = self.client.get(self.url)
        self.assertEqual(len(response.context["versions"]), 2)

class EducationGroupDiplomas(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_year = AcademicYearFactory()
        type_training = EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        cls.education_group_parent = EducationGroupYearFactory(acronym="Parent", academic_year=academic_year,
                                                               education_group_type=type_training)
        cls.education_group_child = EducationGroupYearFactory(acronym="Child_1", academic_year=academic_year,
                                                              education_group_type=type_training)
        GroupElementYearFactory(parent=cls.education_group_parent, child_branch=cls.education_group_child)
        cls.user = UserFactory()
        cls.person = PersonFactory(user=cls.user)
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        cls.url = reverse("education_group_diplomas",
                          args=[cls.education_group_parent.pk, cls.education_group_child.id])

    def setUp(self):
        self.client.force_login(self.user)

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

    def test_with_education_group_year_of_type_mini_training(self):
        mini_training_education_group_year = EducationGroupYearFactory()
        mini_training_education_group_year.education_group_type.category = education_group_categories.MINI_TRAINING
        mini_training_education_group_year.education_group_type.save()

        url = reverse("education_group_diplomas",
                      args=[mini_training_education_group_year.id, mini_training_education_group_year.id])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_with_education_group_year_of_type_group(self):
        group_education_group_year = EducationGroupYearFactory()
        group_education_group_year.education_group_type.category = education_group_categories.GROUP
        group_education_group_year.education_group_type.save()

        url = reverse("education_group_diplomas",
                      args=[group_education_group_year.id, group_education_group_year.id]
                      )
        response = self.client.get(url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_without_get_data(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "education_group/tab_diplomas.html")

        context = response.context
        self.assertEqual(context["education_group_year"], self.education_group_child)
        self.assertEqual(context["parent"], self.education_group_parent)

    def test_with_non_existent_root_id(self):
        non_existent_id = self.education_group_child.id + self.education_group_parent.id
        url = reverse("education_group_diplomas", args=[non_existent_id, self.education_group_child.pk])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "page_not_found.html")
        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_with_root_set(self):
        response = self.client.get(self.url, data={"root": self.education_group_parent.id})

        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, "education_group/tab_diplomas.html")

        context = response.context
        self.assertEqual(context["education_group_year"], self.education_group_child)
        self.assertEqual(context["parent"], self.education_group_parent)

    def test_get_queryset__order_certificate_aims(self):
        self._generate_certificate_aims_with_wrong_order()

        response = self.client.get(self.url, data={"root": self.education_group_parent.id})
        certificate_aims = response.context['education_group_year'].certificate_aims.all()
        expected_order = sorted(certificate_aims, key=lambda obj: (obj.section, obj.code))
        self.assertListEqual(expected_order, list(certificate_aims))

    def _generate_certificate_aims_with_wrong_order(self):
        # Numbers below are used only to ensure records are saved in wrong order (there's no other meaning)
        for section in range(4, 2, -1):
            code_range = section * 11
            for code in range(code_range, code_range-2, -1):
                EducationGroupCertificateAimFactory(
                    education_group_year=self.education_group_child,
                    certificate_aim=CertificateAimFactory(code=code, section=section),
                )


class EducationGroupGeneralInformations(TestCase):
    @classmethod
    def setUpTestData(cls):
        academic_year = AcademicYearFactory()
        cls.current_academic_year = AcademicYearFactory(year=datetime.datetime.now().year)
        cls.type_training = EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        cls.type_minor = EducationGroupTypeFactory(name="ACCESS_MINOR")
        cls.type_deepening = EducationGroupTypeFactory(name="DEEPENING")
        cls.education_group_parent = EducationGroupYearFactory(acronym="Parent", academic_year=academic_year,
                                                               education_group_type=cls.type_training)
        cls.education_group_child = EducationGroupYearFactory(acronym="Child_1", academic_year=academic_year,
                                                              education_group_type=cls.type_training)
        GroupElementYearFactory(parent=cls.education_group_parent, child_branch=cls.education_group_child)

        cls.cms_label_for_child = TranslatedTextFactory(text_label=TextLabelFactory(entity=entity_name.OFFER_YEAR),
                                                        reference=cls.education_group_child.id)

        cls.user = UserFactory()
        cls.person = PersonFactory(user=cls.user)
        cls.user.user_permissions.add(Permission.objects.get(codename="can_access_education_group"))
        cls.url = reverse("education_group_general_informations",
                          args=[cls.education_group_parent.pk, cls.education_group_child.id])

    def setUp(self):
        self.client.force_login(self.user)

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
        group_education_group_year = EducationGroupYearFactory()
        group_education_group_year.education_group_type.category = education_group_categories.GROUP
        group_education_group_year.education_group_type.save()

        url = reverse("education_group_general_informations",
                      args=[group_education_group_year.id, group_education_group_year.id])
        response = self.client.get(url)

        self.assertTemplateUsed(response, "access_denied.html")
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

    def test_without_get_data(self):
        response = self.client.get(self.url)

        self.assertTemplateUsed(response, "education_group/tab_general_informations.html")

        context = response.context
        self.assertEqual(context["parent"], self.education_group_parent)
        self.assertEqual(context["education_group_year"], self.education_group_child)

    @mock.patch('base.views.education_groups.detail.is_eligible_to_edit_general_information', side_effect=lambda p, o: True)
    def test_user_has_link_to_edit_pedagogy(self, mock_is_eligible):
        self.user.user_permissions.add(Permission.objects.get(codename='can_edit_educationgroup_pedagogy'))
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/tab_general_informations.html")

        soup = bs4.BeautifulSoup(response.content, 'html.parser')
        self.assertGreater(len(soup.select('a.pedagogy-edit-btn')), 0)

    def test_user_has_not_link_to_edit_pedagogy(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/tab_general_informations.html")

        soup = bs4.BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(len(soup.select('a.pedagogy-edit-btn')), 0)

    @mock.patch('base.views.education_group.education_group_year_pedagogy_edit_post')
    @mock.patch('base.views.education_group.education_group_year_pedagogy_edit_get')
    @mock.patch('django.contrib.auth.decorators')
    def test_education_group_year_pedagogy_edit(self, mock_decorators, mock_edit_get, mock_edit_post):
        from base.views.education_group import education_group_year_pedagogy_edit
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        root_id = self.education_group_parent.id
        education_group_year_id = self.education_group_child.id

        factory = RequestFactory()
        request = factory.post('/{}/{}/informations/edit/'.format(root_id, education_group_year_id))
        request.user = mock.Mock()
        response = education_group_year_pedagogy_edit(request, root_id, education_group_year_id)

        mock_edit_post.assert_called_once_with(request, education_group_year_id, root_id)

        request = factory.get('/1/2/informations/edit/')
        request.user = mock.Mock()
        response = education_group_year_pedagogy_edit(request, root_id, education_group_year_id)

        mock_edit_get.assert_called_once_with(request, education_group_year_id)

    @mock.patch('base.views.layout.render')
    def test_education_group_year_pedagogy_edit_get(self, mock_render):
        request = RequestFactory().get('/')
        request.user = UserFactory()

        from base.views.education_group import education_group_year_pedagogy_edit_get
        education_group_year_pedagogy_edit_get(request, self.education_group_child.id)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(context['education_group_year'], self.education_group_child)

    @mock.patch('base.views.layout.render')
    def test_education_group_year_pedagogy_edit_get_with_translated_texts(self, mock_render):
        text_label = TextLabelFactory(label='label_abc')
        fr_translated_text = TranslatedTextRandomFactory(reference=str(self.education_group_child.id),
                                                         entity=entity_name.OFFER_YEAR,
                                                         text_label=text_label,
                                                         language='fr-be')
        en_translated_text = TranslatedTextRandomFactory(reference=str(self.education_group_child.id),
                                                         entity=entity_name.OFFER_YEAR,
                                                         text_label=fr_translated_text.text_label,
                                                         language='en')

        request = RequestFactory().get('/?label={}'.format(fr_translated_text.text_label.label))
        request.user = UserFactory()

        from base.views.education_group import education_group_year_pedagogy_edit_get
        education_group_year_pedagogy_edit_get(request, self.education_group_child.id)

        request, template, context = mock_render.call_args[0]

        form = context['form']
        self.assertEqual(form.initial['label'], text_label.label)
        self.assertEqual(form.initial['text_french'], fr_translated_text.text)
        self.assertEqual(form.initial['text_english'], en_translated_text.text)

    def test_education_group_year_pedagogy_edit_post(self):
        form = {
            'label': 'welcome_introduction',
            'text_french': 'Salut',
            'text_english': 'Hello'
        }
        request = RequestFactory().post('/', form)

        from base.views.education_group import education_group_year_pedagogy_edit_post

        response = education_group_year_pedagogy_edit_post(request,
                                                           self.education_group_child.id,
                                                           self.education_group_parent.id)

        self.assertEqual(response.status_code, 302)

    def test_education_group_year_pedagogy_publish_not_found(self):
        url = reverse('education_group_publish', args=(self.education_group_child.id, self.education_group_parent.id))
        response = self.client.get(url)
        msg = [m.message for m in get_messages(response.wsgi_request)]
        msg_level = [m.level for m in get_messages(response.wsgi_request)]
        self.assertEqual(len(msg), 1)
        self.assertIn(messages.ERROR, msg_level)
        self.assertEqual(response.status_code, 302)

    def test_education_group_year_pedagogy_publish_found(self):
        education_group_real = EducationGroupYearFactory(acronym="SINF1BA", academic_year=self.current_academic_year,
                                                         education_group_type=self.type_training)
        url = reverse('education_group_publish', args=(self.education_group_parent.id, education_group_real.id))
        response = self.client.get(url)
        msg = [m.message for m in get_messages(response.wsgi_request)]
        msg_level = [m.level for m in get_messages(response.wsgi_request)]
        self.assertEqual(len(msg), 1)
        self.assertIn(messages.SUCCESS, msg_level)
        self.assertEqual(response.status_code, 302)

    def test_education_group_year_pedagogy_publish_when_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, '/login/?next={}'.format(self.url))

    def test_education_group_year_pedagogy_publish_minor(self):
        education_group_minor = EducationGroupYearFactory(partial_acronym="LALLE100I",
                                                          academic_year=self.current_academic_year,
                                                          education_group_type=self.type_minor)
        url = reverse('education_group_publish', args=(self.education_group_parent.id, education_group_minor.id))
        response = self.client.get(url)
        msg = [m.message for m in get_messages(response.wsgi_request)]
        msg_level = [m.level for m in get_messages(response.wsgi_request)]
        self.assertEqual(len(msg), 1)
        self.assertIn(messages.SUCCESS, msg_level)
        self.assertEqual(response.status_code, 302)

    def test_education_group_year_pedagogy_publish_deepening(self):
        education_group_deep = EducationGroupYearFactory(partial_acronym="LDRT100P",
                                                         academic_year=self.current_academic_year,
                                                         education_group_type=self.type_deepening)
        url = reverse('education_group_publish', args=(self.education_group_parent.id, education_group_deep.id))
        response = self.client.get(url)
        msg = [m.message for m in get_messages(response.wsgi_request)]
        msg_level = [m.level for m in get_messages(response.wsgi_request)]
        self.assertEqual(len(msg), 1)
        self.assertIn(messages.SUCCESS, msg_level)
        self.assertEqual(response.status_code, 302)


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

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    @mock.patch('base.business.education_group.can_user_edit_administrative_data')
    def test_education_edit_administrative_data(self,
                                                mock_can_user_edit_administrative_data,
                                                mock_render,
                                                mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func
        education_group_year = EducationGroupYearFactory(academic_year=self.academic_year)
        from base.views.education_group import education_group_edit_administrative_data

        request_factory = RequestFactory()
        request = request_factory.get(reverse(education_group_edit_administrative_data, kwargs={
            'root_id': education_group_year.id,
            'education_group_year_id': education_group_year.id
        }))
        request.user = mock.Mock()
        mock_can_user_edit_administrative_data.return_value = True

        education_group_edit_administrative_data(request, education_group_year.id, education_group_year.id)
        self.assertTrue(mock_render.called)
        request, template, context = mock_render.call_args[0]
        self.assertEqual(template, 'education_group/tab_edit_administrative_data.html')
        self.assertEqual(context['education_group_year'], education_group_year)
        self.assertEqual(context['course_enrollment_validity'], False)
        self.assertEqual(context['formset_session_validity'], False)
        self.assertIn('additional_info_form', context)

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
class EducationGroupYearEditPedagogy(TestCase):
    def setUp(self):
        self.person = PersonFactory()

        self.permission = Permission.objects.get(codename='can_edit_educationgroup_pedagogy')
        self.person.user.user_permissions.add(self.permission)

        self.education_group_year = EducationGroupYearFactory()

        self.url = reverse('education_group_pedagogy_edit',
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

    def test_user_has_permission(self):
        text_label = TextLabelFactory(entity=entity_name.OFFER_YEAR)

        url = "{}?label={}&language={}".format(self.url, text_label.label, self.person.language)
        response = self.client.get(url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/pedagogy_edit.html")

        soup = bs4.BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(soup.div.form['action'], self.url)


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
        academic_year = AcademicYearFactory()
        type_training = EducationGroupTypeFactory(category=education_group_categories.TRAINING)
        cls.education_group_parent = EducationGroupYearFactory(acronym="Parent", academic_year=academic_year,
                                                               education_group_type=type_training)
        cls.education_group_child = EducationGroupYearFactory(acronym="Child_1", academic_year=academic_year,
                                                              education_group_type=type_training)

        GroupElementYearFactory(parent=cls.education_group_parent, child_branch=cls.education_group_child)

        cls.cms_label_for_child = TranslatedTextFactory(text_label=TextLabelFactory(entity=entity_name.OFFER_YEAR),
                                                        reference=cls.education_group_child.id)

        cls.user = UserFactory()
        cls.person = PersonFactory(user=cls.user)
        cls.user.user_permissions.add(Permission.objects.get(codename="can_edit_educationgroup_pedagogy"))
        cls.url = reverse("education_group_year_admission_condition_edit",
                          args=[cls.education_group_parent.pk, cls.education_group_child.id])

    def setUp(self):
        self.client.force_login(self.user)

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

    @mock.patch('base.views.education_groups.detail.is_eligible_to_edit_general_information', side_effect=lambda p, o: True)
    def test_user_has_link_to_edit_conditions(self, mock_is_eligible):
        self.user.user_permissions.add(Permission.objects.get(codename='can_edit_educationgroup_pedagogy'))
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/tab_admission_conditions.html")

        soup = bs4.BeautifulSoup(response.content, 'html.parser')
        self.assertGreater(len(soup.select('a.btn-publish')), 0)

    def test_user_has_not_link_to_edit_conditions(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponse.status_code)
        self.assertTemplateUsed(response, "education_group/tab_admission_conditions.html")

        soup = bs4.BeautifulSoup(response.content, 'html.parser')
        self.assertEqual(len(soup.select('a.btn-publish')), 0)

    @mock.patch('django.contrib.auth.decorators')
    def test_education_group_year_admission_condition_remove_line_not_found(self, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        from base.views.education_group import education_group_year_admission_condition_remove_line

        root_id = self.education_group_parent.id
        education_group_year_id = self.education_group_child.id
        request = RequestFactory().get('/?id=0')
        request.user = mock.Mock()
        import django.http.response
        with self.assertRaises(django.http.response.Http404):
            response = education_group_year_admission_condition_remove_line(request, root_id, education_group_year_id)

    @mock.patch('django.contrib.auth.decorators')
    def test_education_group_year_admission_condition_remove_line(self, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        from base.views.education_group import education_group_year_admission_condition_remove_line

        root_id = self.education_group_parent.id
        education_group_year_id = self.education_group_child.id
        admission_condition = AdmissionCondition.objects.create(education_group_year=self.education_group_child)
        admission_condition_line = AdmissionConditionLine.objects.create(
            admission_condition=admission_condition
        )
        request = RequestFactory().get('/?id={}'.format(admission_condition_line.id))
        request.user = mock.Mock()
        queryset = AdmissionConditionLine.objects.filter(admission_condition=admission_condition)
        self.assertEqual(queryset.count(), 1)
        response = education_group_year_admission_condition_remove_line(request, root_id, education_group_year_id)
        self.assertEqual(queryset.count(), 0)

    @mock.patch('base.views.education_group.education_group_year_admission_condition_update_line_post')
    @mock.patch('base.views.education_group.education_group_year_admission_condition_update_line_get')
    @mock.patch('django.contrib.auth.decorators')
    def test_education_group_year_admission_condition_update_line(self,
                                                                  mock_decorators,
                                                                  mock_get,
                                                                  mock_post):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        root_id = self.education_group_parent.id
        education_group_year_id = self.education_group_child.id

        factory = RequestFactory()
        request = factory.post('/')
        request.user = mock.Mock()

        from base.views.education_group import education_group_year_admission_condition_update_line
        response = education_group_year_admission_condition_update_line(request, root_id, education_group_year_id)
        mock_post.assert_called_once_with(request, root_id, education_group_year_id)

        request = factory.get('/')
        request.user = mock.Mock()
        response = education_group_year_admission_condition_update_line(request, root_id, education_group_year_id)
        mock_get.assert_called_once_with(request)

    @mock.patch('base.views.education_group.get_content_of_admission_condition_line')
    @mock.patch('base.views.layout.render')
    def test_education_group_year_admission_condition_update_line_get_admission_condition_line_exists(self,
                                                                                                      mock_render,
                                                                                                      mock_get_content):
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
            'language': 'fr',
            'id': admission_condition_line.id,
        }
        request = RequestFactory().get('/?{}'.format(urllib.parse.urlencode(info)))

        from base.views.education_group import education_group_year_admission_condition_update_line_get
        response = education_group_year_admission_condition_update_line_get(request)

        mock_get_content.assert_called_once_with('read', admission_condition_line, '')

    @mock.patch('base.views.education_group.get_content_of_admission_condition_line')
    @mock.patch('base.views.layout.render')
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
        self.assertEqual(response.status_code, 302)

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
        self.assertEqual(response.status_code, 302)

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

    @mock.patch('base.views.education_group.education_group_year_admission_condition_update_text_post')
    @mock.patch('base.views.education_group.education_group_year_admission_condition_update_text_get')
    @mock.patch('django.contrib.auth.decorators')
    def test_education_group_year_admission_condition_update_text(self,
                                                                  mock_decorators,
                                                                  mock_get,
                                                                  mock_post):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        root_id = self.education_group_parent.id
        education_group_year_id = self.education_group_child.id

        request = RequestFactory().post('/')
        request.user = mock.Mock()

        from base.views.education_group import education_group_year_admission_condition_update_text
        response = education_group_year_admission_condition_update_text(request, root_id, education_group_year_id)
        mock_post.assert_called_once_with(request, root_id, education_group_year_id)

        request = RequestFactory().get('/')
        request.user = mock.Mock()
        response = education_group_year_admission_condition_update_text(request, root_id, education_group_year_id)
        mock_get.assert_called_once_with(request, education_group_year_id)

    @mock.patch('base.views.layout.render')
    def test_education_group_year_admission_condition_update_text_get(self,
                                                                      mock_render):
        from base.views.education_group import education_group_year_admission_condition_update_text_get

        info = {
            'section': 'free',
            'language': 'fr',
            'title': 'Free Text',
        }
        request = RequestFactory().get('/?{}'.format(urllib.parse.urlencode(info)))
        request.user = mock.Mock()

        AdmissionCondition.objects.create(education_group_year=self.education_group_child)
        education_group_year_admission_condition_update_text_get(request, self.education_group_child.id)

        unused_request, template_name, context = mock_render.call_args[0]
        self.assertEqual(template_name, 'education_group/condition_text_edit.html')
        self.assertIn('form', context)

    def test_education_group_year_admission_condition_update_text_post_form_is_valid(self):
        root_id = self.education_group_parent.id
        education_group_year_id = self.education_group_child.id

        values = {
            'section': 'free',
            'text_fr': 'Texte en Français',
            'text_en': 'Text in English'
        }
        request = RequestFactory().post('/', values)

        AdmissionCondition.objects.create(education_group_year=self.education_group_child)

        from base.views.education_group import education_group_year_admission_condition_update_text_post
        response = education_group_year_admission_condition_update_text_post(request, root_id, education_group_year_id)

        self.education_group_child.admissioncondition.refresh_from_db()
        self.assertEqual(self.education_group_child.admissioncondition.text_free, values['text_fr'])
        self.assertEqual(self.education_group_child.admissioncondition.text_free_en, values['text_en'])
        self.assertEqual(response.status_code, 302)

    @mock.patch('base.forms.education_group_admission.UpdateTextForm.is_valid', return_value=False)
    def test_education_group_year_admission_condition_update_text_post_form_is_not_valid(self,
                                                                                         mock_is_valid):
        root_id = self.education_group_parent.id
        education_group_year_id = self.education_group_child.id

        request = RequestFactory().post('/')

        from base.views.education_group import education_group_year_admission_condition_update_text_post
        response = education_group_year_admission_condition_update_text_post(request, root_id, education_group_year_id)

        self.assertEqual(response.status_code, 302)

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

        self.assertEqual(response.status_code, 200)

        admission_condition_line_1.refresh_from_db()
        admission_condition_line_2.refresh_from_db()

        self.assertGreater(admission_condition_line_1.order, admission_condition_line_2.order)

        data = {
            'action': 'up',
            'record': admission_condition_line_1.id,
        }

        response = self.client.post(url, data=json.dumps(data), content_type='application/json', **kwargs)

        self.assertEqual(response.status_code, 200)

        admission_condition_line_1.refresh_from_db()
        admission_condition_line_2.refresh_from_db()

        self.assertLess(admission_condition_line_1.order, admission_condition_line_2.order)
