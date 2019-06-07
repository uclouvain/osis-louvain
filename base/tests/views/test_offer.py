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

from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden
from django.test import TestCase

from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.program_manager import ProgramManagerFactory
from base.tests.factories.user import SuperUserFactory


class OfferViewTestCase(TestCase):
    def setUp(self):
        self.superuser = SuperUserFactory()
        self.client.force_login(self.superuser)

    def test_offers(self):
        today = datetime.date.today()
        academic_year = AcademicYearFactory(start_date=today,
                                            end_date=today.replace(year=today.year + 1),
                                            year=today.year)

        response = self.client.get(reverse('offers'))

        self.assertTemplateUsed(response, 'offers.html')
        self.assertEqual(len(response.context['offers']), 0)
        self.assertEqual(response.context['academic_year'], academic_year.id)

    def test_offers_search(self):
        today = datetime.date.today()
        academic_year = AcademicYearFactory(start_date=today,
                                            end_date=today.replace(year=today.year + 1),
                                            year=today.year)

        response = self.client.get(reverse('offers_search'), data={
            'entity_acronym': 'entity',
            'code': 'code',
            'academic_year': academic_year.id,
        })

        self.assertTemplateUsed(response, 'offers.html')
        self.assertEqual(response.context['offer_years'].count(), 0)

    def test_offer_read(self):
        today = datetime.date.today()
        academic_year = AcademicYearFactory(start_date=today,
                                            end_date=today.replace(year=today.year + 1),
                                            year=today.year)
        offer_year = OfferYearFactory(academic_year=academic_year)

        academic_calendar = AcademicCalendarFactory(academic_year=academic_year)

        offer_year_calendar = OfferYearCalendarFactory(offer_year=offer_year,
                                                       academic_calendar=academic_calendar)
        ProgramManagerFactory(offer_year=offer_year)

        response = self.client.get(reverse('offer_read', args=[offer_year.pk]))

        self.assertTemplateUsed(response, 'offer/tab_identification.html')

    @mock.patch('base.models.program_manager')
    def test_offer_year_calendar_read(self, mock_program_manager):
        offer_year = OfferYearCalendarFactory()
        mock_program_manager.is_program_manager.return_value = True

        response = self.client.get(reverse('offer_year_calendar_read', args=[offer_year.id]))

        self.assertTemplateUsed(response, 'offer_year_calendar.html')
        self.assertEqual(response.context['offer_year_calendar'], offer_year)
        self.assertEqual(response.context['is_programme_manager'], mock_program_manager.is_program_manager())

    def test_cannot_access_any_offer_pages_if_not_program_manager(self):
        offer_year = OfferYearCalendarFactory()
        person = PersonFactory()
        self.client.force_login(person.user)
        pages = [
            ('offer_year_calendar_read', offer_year.id),
            ('offer_read', offer_year.pk),
            ('offer_academic_calendar_tab', offer_year.pk),
            ('offer_program_managers_tab', offer_year.pk),
            ('offers_search', None),
            ('offers', None)
        ]
        for page, arg in pages:
            url = reverse(page, args=[arg]) if arg else reverse(page)
            response = self.client.get(url)
            self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
            self.assertTemplateUsed(response, 'access_denied.html')
