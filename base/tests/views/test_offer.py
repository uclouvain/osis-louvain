##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2017 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.test import TestCase, RequestFactory

from base.models.academic_calendar import AcademicCalendar
from base.tests.factories.academic_calendar import AcademicCalendarFactory
from base.tests.factories.academic_year import AcademicYearFactory
from base.tests.factories.offer_year import OfferYearFactory
from base.tests.factories.offer_year_calendar import OfferYearCalendarFactory
from base.tests.factories.program_manager import ProgramManagerFactory


def save(self, *args, **kwargs):
    return super(AcademicCalendar, self).save()


class OfferViewTestCase(TestCase):
    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_offers(self, mock_render, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        today = datetime.date.today()
        academic_year = AcademicYearFactory(start_date=today,
                                            end_date=today.replace(year=today.year + 1),
                                            year=today.year)

        request_factory = RequestFactory()

        request = request_factory.get(reverse('offers'))
        request.user = mock.Mock()

        from base.views.offer import offers

        offers(request)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'offers.html')
        self.assertEqual(len(context['offers']), 0)
        self.assertEqual(context['academic_year'], academic_year.id)

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    def test_offers_search(self, mock_render, mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        request_factory = RequestFactory()
        today = datetime.date.today()
        academic_year = AcademicYearFactory(start_date=today,
                                            end_date=today.replace(year=today.year + 1),
                                            year=today.year)

        request = request_factory.get(reverse('offers_search'), data={
            'entity_acronym': 'entity',
            'code': 'code',
            'academic_year': academic_year.id,
        })
        request.user = mock.Mock()

        from base.views.offer import offers_search
        offers_search(request)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'offers.html')
        self.assertEqual(context['offer_years'].count(), 0)

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    @mock.patch('base.models.program_manager.is_program_manager', return_value=True)
    def test_offer_read(self,
                        mock_program_manager,
                        mock_render,
                        mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        today = datetime.date.today()
        academic_year = AcademicYearFactory(start_date=today,
                                            end_date=today.replace(year=today.year + 1),
                                            year=today.year)
        offer_year = OfferYearFactory(academic_year=academic_year)

        AcademicCalendar.save = save
        academic_calendar = AcademicCalendarFactory(academic_year=academic_year)

        offer_year_calendar = OfferYearCalendarFactory(offer_year=offer_year,
                                                       academic_calendar=academic_calendar)
        ProgramManagerFactory(offer_year=offer_year)

        request = mock.Mock(method='GET')

        from base.views.offer import offer_read

        offer_read(request, offer_year_calendar.id)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'offer.html')

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.models.offer_year')
    @mock.patch('reference.models.country')
    def test_score_encoding_post(self,
                                 mock_country,
                                 mock_offer_year,
                                 mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        offer_year = mock.Mock(id=1)
        mock_offer_year.find_by_id.return_value = offer_year
        country = mock.Mock(id=1)
        mock_country.find_by_id.return_value = country

        request = mock.Mock(method='POST')

        from base.views.offer import score_encoding
        response = score_encoding(request, offer_year.id)

        self.assertTrue(offer_year.save.called)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'ok')
        self.assertTrue(response.has_header('content-type'))
        self.assertEqual(response.get('content-type'), 'text/plain')

    @mock.patch('django.contrib.auth.decorators')
    def test_score_encoding_get(self,
                                mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        offer_year = mock.Mock(id=1)
        request = mock.Mock(method='GET')

        from base.views.offer import score_encoding
        response = score_encoding(request, offer_year.id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'nok')
        self.assertTrue(response.has_header('content-type'))
        self.assertEqual(response.get('content-type'), 'text/plain')

    @mock.patch('django.contrib.auth.decorators')
    @mock.patch('base.views.layout.render')
    @mock.patch('base.models.offer_year_calendar')
    @mock.patch('base.models.program_manager')
    def test_offer_year_calendar_read(self,
                                      mock_program_manager,
                                      mock_offer_year_calendar,
                                      mock_render,
                                      mock_decorators):
        mock_decorators.login_required = lambda x: x
        mock_decorators.permission_required = lambda *args, **kwargs: lambda func: func

        offer_year = mock.Mock(id=1)
        mock_offer_year_calendar.find_by_id.return_value = offer_year

        mock_program_manager.is_program_manager.return_value = True

        request_factory = RequestFactory()
        request = request_factory.get(reverse('offer_year_calendar_read', args=[offer_year.id]))
        request.user = mock.Mock()

        from base.views.offer import offer_year_calendar_read

        offer_year_calendar_read(request, offer_year.id)

        self.assertTrue(mock_render.called)

        request, template, context = mock_render.call_args[0]

        self.assertEqual(template, 'offer_year_calendar.html')
        self.assertEqual(context['offer_year_calendar'], offer_year)
        self.assertEqual(context['is_programme_manager'], mock_program_manager.is_program_manager())
