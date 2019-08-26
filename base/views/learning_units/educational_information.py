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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.forms import formset_factory
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from waffle.decorators import waffle_flag

from base.business.learning_units.educational_information import get_responsible_and_learning_unit_yr_list
from base.business.learning_units.perms import can_learning_unit_year_educational_information_be_udpated
from base.business.learning_units.xls_comparison import get_academic_year_of_reference
from base.business.learning_units.xls_generator import generate_xls_teaching_material
from base.forms.common import TooManyResultsException
from base.forms.learning_unit.comparison import SelectComparisonYears
from base.forms.learning_unit.educational_information.mail_reminder import MailReminderRow, MailReminderFormset
from base.forms.learning_unit.search_form import LearningUnitYearForm
from base.models import academic_calendar
from base.models.academic_year import starting_academic_year
from base.models.enums.academic_calendar_type import SUMMARY_COURSE_SUBMISSION
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.utils.cache import cache_filter
from base.utils.send_mail import send_mail_for_educational_information_update
from base.views.common import check_if_display_message, display_warning_messages, paginate_queryset, \
    display_error_messages
from base.views.learning_units.search import SUMMARY_LIST

SUCCESS_MESSAGE = _('Reminding mails sent')


@login_required
@waffle_flag('educational_information_mailing')
@permission_required('base.can_access_learningunit', raise_exception=True)
def send_email_educational_information_needs_update(request):
    if request.is_ajax():
        list_mail_reminder_formset = formset_factory(form=MailReminderRow,
                                                     formset=MailReminderFormset)
        formset = list_mail_reminder_formset(data=request.POST)

        if formset.is_valid():
            responsible_person_ids = formset.get_checked_responsibles()

            _send_email_to_responsibles(responsible_person_ids)
            return JsonResponse({'as_messages_info': SUCCESS_MESSAGE})

    return HttpResponseRedirect(reverse('learning_units_summary'))


@login_required
@cache_filter(exclude_params=["xls_status"])
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_units_summary_list(request):
    a_user_person = request.user.person
    found_learning_units = LearningUnitYear.objects.none()

    initial_academic_year = starting_academic_year()
    if academic_calendar.is_academic_calendar_has_started(initial_academic_year, SUMMARY_COURSE_SUBMISSION):
        initial_academic_year = initial_academic_year.next()

    search_form = LearningUnitYearForm(request.GET or None, initial={'academic_year_id': initial_academic_year,
                                                                     'with_entity_subordinated': True})
    try:
        if search_form.is_valid():
            found_learning_units = search_form.get_learning_units_and_summary_status(
                requirement_entities=a_user_person.find_main_entities_version,
            )
            check_if_display_message(request, found_learning_units)
    except TooManyResultsException:
        display_error_messages(request, 'too_many_results')

    responsible_and_learning_unit_yr_list = get_responsible_and_learning_unit_yr_list(found_learning_units)

    for luy in found_learning_units:
        luy.errors = can_learning_unit_year_educational_information_be_udpated(learning_unit_year_id=luy)

    if request.GET.get('xls_status') == "xls_teaching_material":
        try:
            return generate_xls_teaching_material(request.user, found_learning_units)
        except ObjectDoesNotExist:
            display_warning_messages(request, _("the list to generate is empty.").capitalize())

    form_comparison = SelectComparisonYears(academic_year=get_academic_year_of_reference(found_learning_units))

    context = {
        'form': search_form,
        'formset': _get_formset(request, responsible_and_learning_unit_yr_list),
        'learning_units_count': found_learning_units.count(),
        'search_type': SUMMARY_LIST,
        'is_faculty_manager': a_user_person.is_faculty_manager,
        'form_comparison': form_comparison,
        'page_obj': found_learning_units,
    }

    return render(request, "learning_units.html", context)


def _send_email_to_responsibles(responsible_person_ids):
    for a_responsible_person_id in responsible_person_ids:
        a_person = get_object_or_404(Person, pk=a_responsible_person_id.get('person'))
        send_mail_for_educational_information_update([a_person],
                                                     a_responsible_person_id.get('learning_unit_years'))


def _get_formset(request, responsible_and_learning_unit_yr_list):
    if responsible_and_learning_unit_yr_list:
        list_mail_reminder_formset = formset_factory(form=MailReminderRow,
                                                     formset=MailReminderFormset,
                                                     extra=len(responsible_and_learning_unit_yr_list))
        return list_mail_reminder_formset(request.POST or None, list_responsible=responsible_and_learning_unit_yr_list)
    return None
