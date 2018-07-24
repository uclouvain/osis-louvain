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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
import itertools
from collections import OrderedDict

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext_lazy as _

from base import models as mdl
from base.business.education_group import create_xls, ORDER_COL, ORDER_DIRECTION, create_xls_administrative_data, \
    PRESIDENTS, SECRETARIES, SIGNATORIES
from base.business.education_groups import perms
from base.forms.education_groups import EducationGroupFilter
from base.forms.search.search_form import get_research_criteria
from base.models.enums import education_group_categories, academic_calendar_type
from base.models.person import Person
from base.views import layout
from base.views.common import paginate_queryset
from base.views.education_groups.detail import get_dates, get_sessions_dates
from base.models.enums import mandate_type as mandate_types


@login_required
@permission_required('base.can_access_education_group', raise_exception=True)
def education_groups(request):
    person = get_object_or_404(Person, user=request.user)
    if request.GET:
        form = EducationGroupFilter(request.GET)
    else:
        current_academic_year = mdl.academic_year.current_academic_year()
        form = EducationGroupFilter(initial={'academic_year': current_academic_year,
                                             'category': education_group_categories.TRAINING})

    object_list = _get_object_list(form, request) if form.is_valid() else []

    if request.GET.get('xls_status') == "xls":
        return create_xls(request.user, object_list, _get_filter_keys(form),
                          {ORDER_COL: request.GET.get('xls_order_col'), ORDER_DIRECTION: request.GET.get('xls_order')})

    if request.GET.get('xls_status') == "xls_administrative":
        return create_xls_administrative_data(request.user, _get_administrative_data(object_list),
                                              _get_filter_keys(form),
                                              {ORDER_COL: request.GET.get('xls_order_col'),
                                               ORDER_DIRECTION: request.GET.get('xls_order')})
    context = {
        'form': form,
        'object_list': paginate_queryset(object_list, request.GET),
        'object_list_count': len(object_list),
        'experimental_phase': True,
        'education_group_cats': education_group_categories,
        'can_create_education_group': perms.is_eligible_to_add_education_group(person=person, education_group=None)
    }

    return layout.render(request, "education_groups.html", context)


def _get_object_list(form, request):
    object_list = form.get_object_list()
    if not _check_if_display_message(request, object_list):
        object_list = []
    return object_list


def _check_if_display_message(request, an_education_groups):
    if not an_education_groups:
        messages.add_message(request, messages.WARNING, _('no_result'))

        return False
    return True


def _get_filter_keys(form):
    return OrderedDict(itertools.chain(get_research_criteria(form)))


def _get_administrative_data(object_list_param):
    object_list = [education_group_yr for education_group_yr in object_list_param if
                   education_group_yr.education_group_type.category == 'TRAINING']
    for education_group_yr in object_list:
        education_group_yr.administrative_data = dict()
        education_group_yr.administrative_data['course_enrollment'] = \
            get_dates(academic_calendar_type.COURSE_ENROLLMENT, education_group_yr)
        education_group_yr.administrative_data['exam_enrollments'] = \
            get_sessions_dates(academic_calendar_type.EXAM_ENROLLMENTS, education_group_yr)
        education_group_yr.administrative_data['scores_exam_submission'] = \
            get_sessions_dates(academic_calendar_type.SCORES_EXAM_SUBMISSION,
                               education_group_yr)
        education_group_yr.administrative_data['dissertation_submission'] = get_sessions_dates(
            academic_calendar_type.DISSERTATION_SUBMISSION,
            education_group_yr)
        education_group_yr.administrative_data['deliberation'] = \
            get_sessions_dates(academic_calendar_type.DELIBERATION,
                               education_group_yr)
        education_group_yr.administrative_data['scores_exam_diffusion'] = \
            get_sessions_dates(academic_calendar_type.SCORES_EXAM_DIFFUSION,
                               education_group_yr)
        _get_mandate_data(education_group_yr)
    return object_list


def _get_mandate_data(education_group_yr_param):
    education_group_yr = education_group_yr_param
    education_group_yr.administrative_data[PRESIDENTS] = \
        mdl.mandatary.find_by_education_group_year_function(education_group_yr, mandate_types.PRESIDENT)
    education_group_yr.administrative_data[SECRETARIES] = \
        mdl.mandatary.find_by_education_group_year_function(education_group_yr, mandate_types.SECRETARY)
    education_group_yr.administrative_data[SIGNATORIES] = \
        mdl.mandatary.find_by_education_group_year_function(education_group_yr, mandate_types.SIGNATORY)
    return education_group_yr
