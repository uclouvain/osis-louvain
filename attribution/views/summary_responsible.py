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
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from attribution import models as mdl_attr
from attribution.business.attribution import get_attributions_list, _set_summary_responsible_to_true
from attribution.business.entity_manager import _append_entity_version
from attribution.business.summary_responsible import search_attributions, get_attributions_data
from base import models as mdl_base
from base.models.entity_manager import is_entity_manager, has_perm_entity_manager


@login_required
@user_passes_test(has_perm_entity_manager)
def search(request):
    entities_manager = mdl_base.entity_manager.find_by_user(request.user)
    # The academic year for summary responsible is the next of current academic year
    academic_year = mdl_base.academic_year.current_academic_year().next()
    _append_entity_version(entities_manager, academic_year)
    context = {"entities_manager": entities_manager, "academic_year": academic_year, "init": "0"}
    if request.GET:
        tutor = request.GET.get('tutor')
        summary_responsible = request.GET.get('summary_responsible')
        course_code = request.GET.get('course_code')
        learning_unit_title = request.GET.get('learning_unit_title')
        attributions = search_attributions(
            entities_manager=entities_manager,
            tutor=tutor,
            summary_responsible=summary_responsible,
            course_code=course_code,
            learning_unit_title=learning_unit_title,
            academic_year=academic_year,
        )
        context.update({
            "dict_attribution": get_attributions_list(attributions, "-summary_responsible"),
            "learning_unit_title": learning_unit_title,
            "course_code": course_code,
            "tutor": tutor,
            "summary_responsible": summary_responsible,
            "init": "1"
        })
    return render(request, 'summary_responsible.html', context)


@login_required
@user_passes_test(is_entity_manager)
def edit(request):
    context = {
        'course_code': request.GET.get('course_code'),
        'learning_unit_title': request.GET.get('learning_unit_title'),
        'tutor': request.GET.get('tutor'),
        'summary_responsible': request.GET.get('summary_responsible')
    }
    learning_unit_year_id = request.GET.get('learning_unit_year').strip('learning_unit_year_')
    attributions_data = get_attributions_data(request.user, learning_unit_year_id, '-summary_responsible')
    context.update(attributions_data)
    return render(request, 'summary_responsible_edit.html', context)


@login_required
@require_http_methods(['POST'])
@user_passes_test(is_entity_manager)
def update(request, pk):
    if request.POST.get('action') == "update":
        mdl_attr.attribution.clear_summary_responsible_by_learning_unit_year(pk)
        if request.POST.get('attribution'):
            attribution_id = request.POST.get('attribution').strip('attribution_')
            attribution = mdl_attr.attribution.find_by_id(attribution_id)
            attributions = mdl_attr.attribution.search(tutor=attribution.tutor,
                                                       learning_unit_year=attribution.learning_unit_year)
            _set_summary_responsible_to_true(attributions)

    return HttpResponseRedirect("{}?course_code={}&learning_unit_title={}&tutor={}&summary_responsible={}"
                                .format(reverse('summary_responsible'),
                                        request.POST.get('course_code', ''),
                                        request.POST.get('learning_unit_title', ''),
                                        request.POST.get('tutor', ''),
                                        request.POST.get('summary_responsible', ''))
                                )
