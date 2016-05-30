##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2016 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################

from django.http import HttpResponse
from base import models as mdl
from reference import models as mdl_ref
from . import layout
from datetime import datetime
from base.forms import OfferYearCalendarForm
from django.utils.translation import ugettext_lazy as _


def offers(request):
    academic_yr = None
    academic_years = mdl.academic_year.find_academic_years()

    academic_year_calendar = mdl.academic_year.current_academic_year()
    if academic_year_calendar:
        academic_yr = academic_year_calendar.id
    return layout.render(request, "offers.html", {'academic_year': academic_yr,
                                                  'academic_years': academic_years,
                                                  'offers': [],
                                                  'init': "1"})


def offers_search(request):
    entity = request.GET['entity_acronym']

    academic_yr = None
    if request.GET['academic_year']:
        academic_yr = int(request.GET['academic_year'])
    acronym = request.GET['code']

    academic_years = mdl.academic_year.find_academic_years()

    offer_years = mdl.offer_year.search(entity=entity, academic_yr=academic_yr, acronym=acronym)

    return layout.render(request, "offers.html", {'academic_year': academic_yr,
                                                  'entity_acronym': entity,
                                                  'code': acronym,
                                                  'academic_years': academic_years,
                                                  'offer_years': offer_years,
                                                  'init': "0"})


def offer_read(request, offer_year_id):
    offer_yr = mdl.offer_year.find_by_id(offer_year_id)
    offer_yr_events = mdl.offer_year_calendar.find_offer_year_calendar(offer_yr)
    program_managers = mdl.program_manager.find_by_offer_year(offer_yr)
    is_program_manager = mdl.program_manager.is_program_manager(request.user, offer_year=offer_yr)
    countries = mdl_ref.country.find_all()
    return layout.render(request, "offer.html", {'offer_year': offer_yr,
                                                 'offer_year_events': offer_yr_events,
                                                 'program_managers': program_managers,
                                                 'is_program_manager': is_program_manager,
                                                 'countries': countries,
                                                 'tab': 0})


def score_encoding(request, offer_year_id):
    if request.method == 'POST':
        offer_yr = mdl.offer_year.find_by_id(offer_year_id)
        offer_yr.recipient = request.POST.get('recipient')
        offer_yr.location = request.POST.get('location')
        offer_yr.postal_code = request.POST.get('postal_code')
        offer_yr.city = request.POST.get('city')
        country_id = request.POST.get('country')
        country = mdl_ref.country.find_by_id(country_id)
        offer_yr.country = country
        offer_yr.phone = request.POST.get('phone')
        offer_yr.fax = request.POST.get('fax')
        offer_yr.save()
        data = "ok"
    else:
        data = "nok"

    return HttpResponse(data, content_type='text/plain')


def offer_year_calendar_read(request, id):
    offer_year_calendar = mdl.offer_year_calendar.find_by_id(id)
    is_programme_manager = mdl.program_manager.is_program_manager(request.user, offer_year=offer_year_calendar.offer_year)
    return layout.render(request, "offer_year_calendar.html", {'offer_year_calendar':   offer_year_calendar,
                                                               'is_programme_manager' : is_programme_manager})


def offer_year_calendar_save(request, id):
    form = OfferYearCalendarForm(data=request.POST)

    if id:
        offer_year_calendar = mdl.offer_year_calendar.find_by_id(id)
    else:
        offer_year_calendar = mdl.offer_year_calendar.OfferYearCalendar()

    # validate
    validation = True
    if form.is_valid():
        academic_calendar = mdl.academic_calendar.find_academic_calendar_by_id(request.POST['academic_calendar'])
        offer_year_calendar.academic_calendar=academic_calendar
        if request.POST['start_date']:
            offer_year_calendar.start_date = datetime.strptime(request.POST['start_date'], '%d/%m/%Y')
        else:
            offer_year_calendar.start_date = None

        if request.POST['end_date']:
            offer_year_calendar.end_date = datetime.strptime(request.POST['end_date'], '%d/%m/%Y')
        else:
            offer_year_calendar.end_date = None

        if offer_year_calendar.start_date and offer_year_calendar.end_date:
            if offer_year_calendar.start_date > offer_year_calendar.end_date:
                form.errors['start_date'] = _('begin_date_lt_end_date')
                validation = False
    else:
        validation = False

    if validation:
        offer_year_calendar.customized=True
        offer_year_calendar.save()
        return offer_read(request, offer_year_calendar.offer_year.id)
    else:
        return layout.render(request, "offer_year_calendar_form.html", {'offer_year_calendar': offer_year_calendar,
                                                                        'form': form})


def offer_year_calendar_edit(request, id):
    offer_year_calendar = mdl.offer_year_calendar.find_by_id(id)
    return layout.render(request, "offer_year_calendar_form.html", {'offer_year_calendar': offer_year_calendar})
