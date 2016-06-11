##############################################################################
#
# OSIS stands for Open Student Information System. It's an application
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
from datetime import datetime

from django.contrib import messages
from django.shortcuts import get_object_or_404
from base.forms import AcademicCalendarForm
from base import models as mdl
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext as trans
from . import layout


def academic_calendars(request):
    academic_year = None
    academic_years = mdl.academic_year.find_academic_years()

    academic_year_calendar = mdl.academic_year.current_academic_year()
    if academic_year_calendar:
        academic_year = academic_year_calendar.id
    academic_calendars = mdl.academic_calendar.find_academic_calendar_by_academic_year(academic_year)
    return layout.render(request, "academic_calendars.html", {'academic_year': academic_year,
                                                              'academic_years': academic_years,
                                                              'academic_calendars': academic_calendars})


def academic_calendars_search(request):
    academic_year = request.GET['academic_year']
    academic_years = mdl.academic_year.find_academic_years()

    if academic_year is None:
        academic_year_calendar = mdl.academic_year.current_academic_year()
        if academic_year_calendar:
            academic_year = academic_year_calendar.id

    query = mdl.academic_calendar.find_academic_calendar_by_academic_year(academic_year)

    return layout.render(request, "academic_calendars.html", {
        'academic_year': int(academic_year),
        'academic_years': academic_years,
        'academic_calendars': query})


def academic_calendar_read(request, id):
    academic_calendar = mdl.academic_calendar.find_academic_calendar_by_id(id)
    return layout.render(request, "academic_calendar.html", {'academic_calendar': academic_calendar})


def academic_calendar_new(request):
    return academic_calendar_save(request, None)


def academic_calendar_save(request, id):
    form = AcademicCalendarForm(data=request.POST)

    if id:
        academic_calendar = mdl.academic_calendar.find_academic_calendar_by_id(id)
    else:
        academic_calendar = mdl.academic_calendar.AcademicCalendar()
    academic_year = None
    academic_year_id = request.POST['academic_year']

    # get the screen modifications
    if academic_year_id:
        academic_year = get_object_or_404(mdl.academic_year.AcademicYear, pk=academic_year_id)
        academic_calendar.academic_year = academic_year
    else:
        academic_calendar.academic_year = None

    academic_calendars = mdl.academic_calendar.find_academic_calendar_by_academic_year(academic_year)

    if request.POST['title']:
        academic_calendar.title = request.POST['title']
    else:
        academic_calendar.title = None

    if request.POST['description']:
        academic_calendar.description = request.POST['description']
    else:
        academic_calendar.description = None

    if request.POST['highlight_description']:
        academic_calendar.highlight_description = request.POST['highlight_description']
    else:
        academic_calendar.highlight_description = None

    if request.POST['highlight_title']:
        academic_calendar.highlight_title = request.POST['highlight_title']
    else:
        academic_calendar.highlight_title = None

    if request.POST['highlight_shortcut']:
        academic_calendar.highlight_shortcut = request.POST['highlight_shortcut']
    else:
        academic_calendar.highlight_shortcut = None

    academic_years = mdl.academic_year.find_academic_years()
    if form.is_valid():
        if request.POST['start_date']:
            academic_calendar.start_date = datetime.strptime(request.POST['start_date'], '%d/%m/%Y')
        else:
            academic_calendar.start_date = None

        if request.POST['end_date']:
            academic_calendar.end_date = datetime.strptime(request.POST['end_date'], '%d/%m/%Y')
        else:
            academic_calendar.end_date = None

        if academic_calendar.start_date and academic_calendar.end_date:
            if academic_calendar.start_date > academic_calendar.end_date:
                form.errors['start_date'] = _('begin_date_lt_end_date')

        new_academic_calendar = False
        if academic_calendar.id is None:
            new_academic_calendar = True
        off_year_calendar_min = mdl.offer_year_calendar.get_min_start_date(academic_calendar.id)
        off_year_calendar_max = mdl.offer_year_calendar.get_max_end_date(academic_calendar.id)
        if academic_calendar.start_date.date() > off_year_calendar_min.start_date:
            messages.add_message(request,
                                 messages.ERROR,
                                 "%s" % (trans('academic_calendar_offer_year_calendar_start_date_error')
                                         % (off_year_calendar_min.start_date.strftime('%d/%m/%Y'),
                                            off_year_calendar_min.offer_year.acronym)))
            return layout.render(request, "academic_calendar_form.html", {'academic_calendar': academic_calendar,
                                                                          'academic_years': academic_years,
                                                                          'form': form})
        elif academic_calendar.end_date.date() < off_year_calendar_max.end_date:
            messages.add_message(request, messages.ERROR,
                                 "%s." % (trans('academic_calendar_offer_year_calendar_end_date_error')
                                          % (off_year_calendar_max.end_date.strftime('%d/%m/%Y'),
                                             off_year_calendar_max.offer_year.acronym)))
            return layout.render(request, "academic_calendar_form.html", {'academic_calendar': academic_calendar,
                                                                          'academic_years': academic_years,
                                                                          'form': form})
        else:
            academic_calendar.save()
            if new_academic_calendar:
                mdl.offer_year_calendar.save(academic_calendar)
            else:
                mdl.offer_year_calendar.update(academic_calendar)
                sent_error_message = mdl.offer_year_calendar.update(academic_calendar)
                if sent_error_message:
                    messages.add_message(request, messages.ERROR, "%s" % sent_error_message)

        return layout.render(request, "academic_calendars.html", {'academic_year': academic_year,
                                                                  'academic_years': academic_years,
                                                                  'academic_calendars': academic_calendars})
    else:
        return layout.render(request, "academic_calendar_form.html", {'academic_calendar': academic_calendar,
                                                                      'academic_years': academic_years,
                                                                      'form': form})


def academic_calendar_edit(request, id):
    academic_calendar = mdl.academic_calendar.find_academic_calendar_by_id(id)
    academic_years = mdl.academic_year.find_academic_years()
    return layout.render(request, "academic_calendar_form.html", {'academic_calendar': academic_calendar,
                                                                  'academic_years': academic_years})


def academic_calendar_create(request):
    academic_calendar = mdl.academic_calendar.AcademicCalendar()
    academic_years = mdl.academic_year.find_academic_years()
    return layout.render(request, "academic_calendar_form.html", {'academic_calendar': academic_calendar,
                                                                  'academic_year': None,
                                                                  'academic_years': academic_years})
