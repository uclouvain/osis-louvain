##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
import json
from unittest import mock

from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseNotFound, HttpResponse, HttpResponseRedirect
from django.test import TestCase, RequestFactory
from django.urls import reverse

from base.forms.education_group_pedagogy_edit import EducationGroupPedagogyEditForm
from base.models.admission_condition import AdmissionCondition, AdmissionConditionLine, CONDITION_ADMISSION_ACCESSES
from base.models.enums.education_group_types import TrainingType
from base.tests.factories.academic_year import AcademicYearFactory, create_current_academic_year
from base.tests.factories.admission_condition import AdmissionConditionFactory
from base.tests.factories.education_group_year import TrainingFactory, EducationGroupYearCommonAgregationFactory, \
    EducationGroupYearCommonBachelorFactory, \
    EducationGroupYearCommonSpecializedMasterFactory, EducationGroupYearCommonMasterFactory
from base.tests.factories.person import PersonFactory
from cms.enums import entity_name
from cms.tests.factories.text_label import OfferTextLabelFactory
from cms.tests.factories.translated_text import TranslatedTextRandomFactory, \
    OfferTranslatedTextFactory
from education_group.tests.factories.group_year import GroupYearFactory
from program_management.tests.factories.education_group_version import StandardEducationGroupVersionFactory
from program_management.tests.factories.element import ElementFactory

ACCESS_DENIED = "access_denied.html"
LOGIN_NEXT = '/login/?next={}'


class EducationGroupPedagogyUpdateViewTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.current_academic_year = create_current_academic_year()
        cls.training = TrainingFactory(
            academic_year=cls.current_academic_year,
            education_group_type__name=TrainingType.PGRM_MASTER_120.name
        )
        version = StandardEducationGroupVersionFactory(
            offer=cls.training,
            root_group__academic_year=cls.current_academic_year,
            root_group__education_group_type=cls.training.education_group_type,
            root_group__partial_acronym=cls.training.partial_acronym
        )
        element = ElementFactory(group_year=version.root_group)
        cls.text_label = OfferTextLabelFactory(label='dummy-label')
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
        cls.person = PersonFactory()
        cls.url = reverse("group_general_information_update", args=[
            element.group_year.academic_year.year,
            element.group_year.partial_acronym
        ])

    def setUp(self):
        self.perm_patcher = mock.patch("django.contrib.auth.models.User.has_perm", return_value=True)
        self.mocked_perm = self.perm_patcher.start()
        self.addCleanup(self.perm_patcher.stop)
        self.client.force_login(self.person.user)

    def test_when_not_logged(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertRedirects(response, LOGIN_NEXT.format(self.url))

    @mock.patch("django.contrib.auth.models.User.has_perm", return_value=False)
    @mock.patch('base.views.education_group.education_group_year_pedagogy_edit_get')
    @mock.patch('base.views.education_group.education_group_year_pedagogy_edit_post')
    def test_get_pedagogy_info_case_user_without_permission(self, mock_edit_post, mock_edit_get, mock_perms):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

        self.assertFalse(mock_edit_post.called)
        self.assertFalse(mock_edit_get.called)

    def test_get_pedagogy_info_case_user_with_permission(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HttpResponse.status_code)

    @mock.patch('base.views.education_group.render')
    def test_get_pedagogy_info_ensure_context_data(self, mock_render):
        response = self.client.get(self.url, data={'label': self.text_label.label})
        request = response.wsgi_request
        context = response.context_data
        request.user = self.person.user
        self.assertEqual(context['label'], self.text_label.label)

        form = context['form']
        self.assertIsInstance(form, EducationGroupPedagogyEditForm)
        self.assertEqual(form.initial['label'], self.text_label.label)
        self.assertEqual(form.initial['text_french'], self.translated_text_in_french.text)
        self.assertEqual(form.initial['text_english'], self.translated_text_in_english.text)

    @mock.patch("django.contrib.auth.models.User.has_perm", return_value=False)
    @mock.patch('base.views.education_group.education_group_year_pedagogy_edit_get')
    @mock.patch('base.views.education_group.education_group_year_pedagogy_edit_post')
    def test_post_pedagogy_info_case_user_without_permission(self, mock_edit_post, mock_edit_get, mock_perms):
        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, HttpResponseForbidden.status_code)

        self.assertFalse(mock_edit_post.called)
        self.assertFalse(mock_edit_get.called)

    def test_post_pedagogy_info_case_user_with_permission(self):
        response = self.client.post(self.url, data={})
        self.assertEqual(response.status_code, HttpResponse.status_code)

    def test_education_group_year_pedagogy_edit_post(self):
        post_data = {'label': 'welcome_introduction', 'text_french': 'Salut', 'text_english': 'Hello'}

        response = self.client.post(self.url, data=post_data)
        json_response = response.json()

        self.assertEqual(response.status_code, HttpResponse.status_code)
        anchor_expected = '#section_welcome_introduction'
        self.assertIn(anchor_expected, json_response['success_url'])


class AdmissionConditionEducationGroupYearTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.academic_year = AcademicYearFactory(current=True)
        cls.education_group_parent = TrainingFactory(
            education_group_type__name=TrainingType.PGRM_MASTER_120.name,  # Type to match 'show_admission_conditions'
            acronym="Parent",
            academic_year=cls.academic_year
        )
        GroupYearFactory(
            partial_acronym=cls.education_group_parent.partial_acronym,
            academic_year=cls.education_group_parent.academic_year,
        )
        cls.education_group_child = TrainingFactory(
            education_group_type__name=TrainingType.MASTER_MC.name,  # Type to match 'show_admission_conditions'
            acronym="Child_1",
            academic_year=cls.academic_year
        )
        GroupYearFactory(
            partial_acronym=cls.education_group_child.partial_acronym,
            academic_year=cls.education_group_child.academic_year,
        )

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
        cls.cms_label_for_child = OfferTranslatedTextFactory(reference=cls.education_group_child.id)

        cls.person = PersonFactory()
        cls.template_name = "education_group/tab_admission_conditions.html"

    def setUp(self):
        self.perm_patcher = mock.patch("django.contrib.auth.models.User.has_perm", return_value=True)
        self.mocked_perm = self.perm_patcher.start()
        self.addCleanup(self.perm_patcher.stop)

        self.client.force_login(self.person.user)

    def test_case_admission_condition_remove_line_not_found(self):
        delete_url = reverse(
            "education_group_year_admission_condition_remove_line",
            args=[self.education_group_child.academic_year.year, self.education_group_child.partial_acronym]
        )
        response = self.client.get(delete_url, data={'id': 0})

        self.assertEqual(response.status_code, HttpResponseNotFound.status_code)

    def test_case_admission_condition_remove_line(self):
        delete_url = reverse(
            "education_group_year_admission_condition_remove_line",
            args=[self.education_group_child.academic_year.year, self.education_group_child.partial_acronym]
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
            args=[self.education_group_child.academic_year.year, self.education_group_child.partial_acronym]
        )
        response = self.client.get(update_url)
        self.assertEqual(response.status_code, HttpResponse.status_code)

        self.assertFalse(mock_edit_post.called)
        self.assertTrue(mock_edit_get.called)


    @mock.patch("django.contrib.auth.models.User.has_perm", return_value=False)
    @mock.patch('base.views.education_group.education_group_year_admission_condition_update_text_post')
    @mock.patch('base.views.education_group.education_group_year_admission_condition_update_text_get')
    def test_case_update_text_admission_condition_without_perms(self, mock_update_get, mock_update_post, mock_perms):
        update_url = reverse(
            "education_group_year_admission_condition_update_text",
            args=[self.education_group_child.academic_year.year, self.education_group_child.partial_acronym]
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
            args=[self.education_group_child.academic_year.year, self.education_group_child.partial_acronym]
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
            args=[self.education_group_child.academic_year.year, self.education_group_child.partial_acronym]
        )
        response = self.client.post(update_url)
        self.assertEqual(response.status_code, HttpResponse.status_code)

        self.assertTrue(mock_update_post.called)
        self.assertFalse(mock_update_get.called)

    def test_webservice_education_group_year_admission_condition_line_order(self):
        kwargs = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

        admission_condition = AdmissionCondition.objects.create(education_group_year=self.education_group_child)

        admission_condition_line_1 = AdmissionConditionLine.objects.create(admission_condition=admission_condition)
        admission_condition_line_2 = AdmissionConditionLine.objects.create(admission_condition=admission_condition)

        self.assertLess(admission_condition_line_1.order, admission_condition_line_2.order)

        url = reverse('education_group_year_admission_condition_line_order', kwargs={
            'year': self.education_group_child.academic_year.year,
            'code': self.education_group_child.partial_acronym,
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
        url = reverse('tab_lang_edit', args=[self.education_group_child.academic_year.year,
                                             self.education_group_child.partial_acronym, 'fr'])
        response = self.client.get(url)
        self.assertEqual(response.status_code, HttpResponseRedirect.status_code)
