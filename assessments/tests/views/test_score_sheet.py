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

from django.test import TestCase
from django.urls import reverse

from assessments.forms.score_sheet_address import ScoreSheetAddressForm
from assessments.views import score_sheet
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.user import SuperUserFactory


class OfferScoreSheetTabViewTest(TestCase):

    def setUp(self):
        today = datetime.date.today()
        self.academic_year = AcademicYearFactory(start_date=today,
                                                 end_date=today.replace(year=today.year + 1),
                                                 year=today.year)
        self.offer_year = OfferYearFactory(academic_year=self.academic_year)
        self.COMMON_CONTEXT_KEYS = ['offer_year', 'countries', 'is_program_manager', 'entity_versions']

    def test_get_common_context(self):
        request = mock.Mock(method='GET')
        context = score_sheet._get_common_context(request, self.offer_year.id)
        self.assert_list_contains(list(context.keys()), self.COMMON_CONTEXT_KEYS)

    def test_offer_score_encoding_tab(self):
        self.client.force_login(SuperUserFactory())
        response = self.client.get(reverse('offer_score_encoding_tab', args=[self.offer_year.id]))

        self.assertTemplateUsed(response, 'offer/score_sheet_address_tab.html')
        context_keys = self.COMMON_CONTEXT_KEYS + ['entity_id_selected', 'form']
        self.assert_list_contains(list(response.context.keys()), context_keys)
        self.assertEqual(response.context['offer_year'], self.offer_year)

    def assert_list_contains(self, container, member):
        self.assertFalse([item for item in member if item not in container])

    @mock.patch('assessments.business.score_encoding_sheet.save_address_from_entity')
    @mock.patch('django.contrib.messages.add_message')
    def test_save_score_sheet_address_case_reuse_entity_address(self,
                                                                mock_add_message,
                                                                mock_save_address_from_entity):
        self.a_superuser = SuperUserFactory()
        self.client.force_login(self.a_superuser)
        url = reverse('save_score_sheet_address', args=[self.offer_year.id])
        response = self.client.post(url, data={'related_entity': 1234})
        self.assertTrue(mock_add_message.called)
        self.assertEqual(response.url, reverse('offer_score_encoding_tab', args=[self.offer_year.id]))

    @mock.patch('assessments.views.score_sheet._save_customized_address')
    def test_save_score_sheet_address_case_customized_address(self, mock_save_customized_address):
        self.client.force_login(SuperUserFactory())

        mock_save_customized_address.return_value = ScoreSheetAddressForm()

        response = self.client.post(reverse('save_score_sheet_address', args=[self.offer_year.id]))

        self.assertTemplateUsed(response, 'offer/score_sheet_address_tab.html')
        self.assert_list_contains(list(response.context.keys()), self.COMMON_CONTEXT_KEYS + ['form'])
