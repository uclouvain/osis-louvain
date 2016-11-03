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
from django.contrib.auth.decorators import login_required, permission_required

from django.http import HttpResponse
from base import models as mdl
from base.forms.offer_form import OfferFormForm
from base.forms.offer_question import OfferQuestionForm
from admission import models as admission
from reference import models as mdl_ref
from . import layout
from datetime import datetime
from base.forms.offer_year_calendar import OfferYearCalendarForm
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.shortcuts import get_object_or_404


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
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


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
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


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def offer_read(request, offer_year_id):
    offer_yr = mdl.offer_year.find_by_id(offer_year_id)
    offer_yr_events = mdl.offer_year_calendar.find_by_offer_year(offer_yr)
    admission_form = admission.form.find_by_offer_year(offer_yr)
    program_managers = mdl.program_manager.find_by_offer_year(offer_yr)
    is_program_manager = mdl.program_manager.is_program_manager(request.user, offer_year=offer_yr)
    countries = mdl_ref.country.find_all()
    displaytab = request.GET.get('displaytab', '')
    return layout.render(request, "offer.html", {'offer_year': offer_yr,
                                                 'offer_year_events': offer_yr_events,
                                                 'admission_form': admission_form,
                                                 'program_managers': program_managers,
                                                 'is_program_manager': is_program_manager,
                                                 'is_admission_form': True,
                                                 'displaytab': displaytab,
                                                 'countries': countries,
                                                 'tab': 0})


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
@permission_required('base.can_access_scoreencoding', raise_exception=True)
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


def offer_question_read(request, question_id):
    question = admission.question.find_by_id(question_id)
    options = admission.option.find_by_question_id(question)
    is_programme_manager = mdl.program_manager.is_program_manager(request.user, offer_year=question.form.offer_year)
    return layout.render(request, "offer_question.html", {'question': question,
                                                          'options': options,
                                                          'questions_types': admission.question.QUESTION_TYPES,
                                                          'is_programme_manager': is_programme_manager})


def offer_question_create(request, form_id):
    question = admission.question.Question()
    question.form = admission.form.find_by_id(form_id)
    return layout.render(request, "offer_question_form.html", {'question': question,
                                                               'questions_types': admission.question.QUESTION_TYPES,
                                                               'form_id': form_id})


def offer_question_edit(request, question_id):
    question = admission.question.find_by_id(question_id)
    options = admission.option.find_by_question_id(question)
    return layout.render(request, "offer_question_form.html", {'question': question,
                                                               'options': options,
                                                               'questions_types': admission.question.QUESTION_TYPES,
                                                               'form_id': question.form.id})


def offer_question_new(request):
    return offer_question_save(request, None)


def offer_question_save(request, question_id=None):

    question = admission.question.find_by_id(question_id)
    question_form = OfferQuestionForm(data=request.POST, instance=question)

    if question_form.is_valid():
        instance = question_form.save()

        #Remove offer_option
        if question_id:
            options = admission.option.find_by_question_id(question_id)
            if options:
                options.delete()

        #loop count total row
        cptlocal = 0
        for key in request.POST:
            foundlabelquest = key.startswith('labelQuest')
            if foundlabelquest == True:
                cptlocal = cptlocal + 1

        #loop request.POST
        maxcpt = 0
        if request.POST['type'] == 'RADIO_BUTTON' or request.POST['type'] == 'CHECKBOX':
            maxcpt = cptlocal
        if request.POST['type'] == 'DROPDOWN_LIST':
            maxcpt = cptlocal

        if maxcpt > 0:

            for cpt in range(1, maxcpt+1):
                offer_option = admission.option.Option()
                offer_option.question = instance

                for key in request.POST:
                    valuelabelquest = request.POST.get('labelQuest'+str(cpt))
                    valuevaluequest = request.POST.get('valueQuest'+str(cpt))
                    valueorderquest = request.POST.get('orderQuest'+str(cpt))
                    valuedescquest = request.POST.get('descQuest'+str(cpt))

                    if valuelabelquest:
                        offer_option.label = valuelabelquest
                    if valuevaluequest:
                        offer_option.value = valuevaluequest
                    if valueorderquest:
                        offer_option.order = valueorderquest
                    if valuedescquest:
                        offer_option.description = valuedescquest

                offer_option.save()

        return offer_question_read(request, instance.id)
    else:
        return layout.render(request, "offer_question_form.html", {'form': question_form,
                                                                   'question': question_form,
                                                                   'form_id': question_form.id,
                                                                   'questions_types': admission.question.QUESTION_TYPES})


def offer_form_read(request, id):
    offer_form = admission.form.find_by_id(id)
    questions = admission.question.find_by_offer_form(offer_form)
    is_programme_manager = mdl.program_manager.is_program_manager(request.user, offer_year=offer_form.offer_year)
    return layout.render(request, "offer_form.html", {'offer_form': offer_form,
                                                      'questions': questions,
                                                      'is_programme_manager': is_programme_manager})


def offer_form_create(request, offer_year_id):
    offer_form = admission.form.Form()
    offer_year = get_object_or_404(mdl.offer_year.OfferYear, pk=offer_year_id)
    return layout.render(request, "offer_form_form.html", {'offer_form': offer_form,
                                                           'offer_year': offer_year,
                                                           'offer_year_id': offer_year_id})


def offer_form_new(request):
    return offer_form_save(request, None)


def offer_form_save(request, form_id):

    offer = admission.form.find_by_id(form_id)
    offer_form = OfferFormForm(data=request.POST, instance=offer)

    if offer_form.is_valid():
        instance = offer_form.save()
        return offer_form_read(request, instance.id)
    else:
        return layout.render(request, "offer_form_form.html", {'offer_form': offer_form,
                                                               'offer_year': offer_form.offer_year,
                                                               'form': offer_form})


def offer_form_edit(request, id):
    offer_form = admission.form.find_by_id(id)
    offer_year = offer_form.offer_year
    return layout.render(request, "offer_form_form.html", {'offer_year': offer_year,
                                                           'offer_form': offer_form})


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def offer_year_calendar_read(request, id):
    offer_year_calendar = mdl.offer_year_calendar.find_by_id(id)
    is_programme_manager = mdl.program_manager.is_program_manager(request.user, offer_year=offer_year_calendar.offer_year)
    return layout.render(request, "offer_year_calendar.html", {'offer_year_calendar':   offer_year_calendar,
                                                               'is_programme_manager': is_programme_manager})


@login_required
@permission_required('base.can_access_offer', raise_exception=True)
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
        offer_year_calendar.academic_calendar = academic_calendar
        if request.POST['start_date']:
            offer_year_calendar.start_date = datetime.strptime(request.POST['start_date'], '%d/%m/%Y')
        else:
            offer_year_calendar.start_date = None

        if request.POST['end_date']:
            offer_year_calendar.end_date = datetime.strptime(request.POST['end_date'], '%d/%m/%Y')
        else:
            offer_year_calendar.end_date = None

        if offer_year_calendar.start_date and offer_year_calendar.end_date:
            if academic_calendar.start_date > offer_year_calendar.start_date.date():
                validation = False
                messages.add_message(request,
                                     messages.ERROR,
                                     "%s (%s)." % (_('offer_year_calendar_academic_calendar_start_date_error'),
                                                   academic_calendar.start_date.strftime('%d/%m/%Y')))
            if academic_calendar.end_date < offer_year_calendar.end_date.date():
                validation = False
                messages.add_message(request, messages.ERROR,
                                     "%s (%s)." % (_('offer_year_calendar_academic_calendar_end_date_error'),
                                                   academic_calendar.end_date.strftime('%d/%m/%Y')))
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

@login_required
@permission_required('base.can_access_offer', raise_exception=True)
def offer_year_calendar_edit(request, id):
    offer_year_calendar = mdl.offer_year_calendar.find_by_id(id)
    return layout.render(request, "offer_year_calendar_form.html", {'offer_year_calendar': offer_year_calendar})