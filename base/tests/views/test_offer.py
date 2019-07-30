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

from django.http import HttpResponseForbidden
from django.test import TestCase
from django.urls import reverse

from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.person import PersonFactory
from base.tests.factories.user import SuperUserFactory


class OfferViewTestCase(TestCase):
    def setUp(self):
        self.superuser = SuperUserFactory()
        self.client.force_login(self.superuser)

    def test_offers(self):
        academic_year = AcademicYearFactory(current=True)

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

    def test_cannot_access_any_offer_pages_if_not_program_manager(self):
        offer_year = OfferYearCalendarFactory()
        person = PersonFactory()
        self.client.force_login(person.user)
        pages = [
            ('offers_search', None),
            ('offers', None),
            ('offer_score_encoding_tab', offer_year.pk)
        ]
        for page, arg in pages:
            url = reverse(page, args=[arg]) if arg else reverse(page)
            response = self.client.get(url)
            self.assertEqual(response.status_code, HttpResponseForbidden.status_code)
            self.assertTemplateUsed(response, 'access_denied.html')