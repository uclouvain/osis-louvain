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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
##############################################################################
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from attribution import models as mdl_attr
from base import models as mdl_base
from base.models.entity_manager import is_entity_manager
from base.views import layout


@login_required
@user_passes_test(is_entity_manager)
def scores_responsible(request):
    entities_manager = mdl_base.entity_manager.find_by_user(request.user)
    academic_year = mdl_base.academic_year.current_academic_year()
    return layout.render(request, 'scores_responsible.html', {"entities_manager": entities_manager,
                                                              "academic_year": academic_year,
                                                              "init": "0"})


@login_required
@user_passes_test(is_entity_manager)
def scores_responsible_search(request):
    entities_manager = mdl_base.entity_manager.find_by_user(request.user)
    attributions = mdl_attr.attribution.find_all_distinct_parents(entities_manager)
    academic_year = mdl_base.academic_year.current_academic_year()
    if request.GET:
        attributions_searched = mdl_attr.attribution.search_scores_responsible(
            learning_unit_title=request.GET.get('learning_unit_title'),
            course_code=request.GET.get('course_code'),
            attributions=attributions,
            tutor=request.GET.get('tutor'),
            responsible=request.GET.get('scores_responsible'))
        dict_attribution = create_attributions_list(attributions_searched)
        return layout.render(request, 'scores_responsible.html', {"entities_manager": entities_manager,
                                                                  "academic_year": academic_year,
                                                                  "dict_attribution": dict_attribution,
                                                                  "learning_unit_title": request.GET.get('learning_unit_title'),
                                                                  "course_code": request.GET.get('course_code'),
                                                                  "tutor": request.GET.get('tutor'),
                                                                  "scores_responsible": request.GET.get('scores_responsible'),
                                                                  "init": "1"})
    else:
        return layout.render(request, 'scores_responsible.html', {"entities_manager": entities_manager,
                                                                  "academic_year": academic_year,
                                                                  "init": "0"})


def create_attributions_list(attributions):
    dict_attribution = dict()
    for attribution in attributions:
        tutors = mdl_attr.attribution.find_all_tutors_by_learning_unit_year(attribution.learning_unit_year)
        dict_attribution[attribution] = [attribution.learning_unit_year.id,
                                         attribution.learning_unit_year.structure.acronym,
                                         attribution.learning_unit_year.acronym,
                                         attribution.learning_unit_year.title,
                                         tutors]
    return dict_attribution


@login_required
@user_passes_test(is_entity_manager)
def scores_responsible_management(request):
    entities_manager = mdl_base.entity_manager.find_by_user(request.user)
    learning_unit_year_id = request.GET.get('learning_unit_year').strip('learning_unit_year_')
    a_learning_unit_year = mdl_base.learning_unit_year.find_by_id(learning_unit_year_id)
    attributions = mdl_attr.attribution.find_all_distinct_parents(entities_manager)
    entities_list = [attribution.learning_unit_year.structure.acronym for attribution in attributions]
    if a_learning_unit_year.structure.acronym in entities_list:
        attributions = mdl_attr.attribution.find_all_responsible_by_learning_unit_year(a_learning_unit_year)
        academic_year = mdl_base.academic_year.current_academic_year()
        return layout.render(request, 'scores_responsible_edit.html',
                             {'learning_unit_year': a_learning_unit_year,
                              'attributions': attributions,
                              "academic_year": academic_year,
                              'course_code': request.GET.get('course_code'),
                              'learning_unit_title': request.GET.get('learning_unit_title'),
                              'tutor': request.GET.get('tutor'),
                              'scores_responsible': request.GET.get('scores_responsible')})
    else:
        return HttpResponseRedirect(reverse('access_denied'))


@login_required
@user_passes_test(is_entity_manager)
def scores_responsible_add(request, pk):
    if request.POST.get('action') == "add":
        a_learning_unit_year = mdl_base.learning_unit_year.find_by_id(pk)
        mdl_attr.attribution.clear_responsible_by_learning_unit_year(a_learning_unit_year)
        if request.POST.get('attribution'):
            attribution_id = request.POST.get('attribution').strip('attribution_')
            attribution = mdl_attr.attribution.find_by_id(attribution_id)
            attributions = mdl_attr.attribution.Attribution.objects \
                .filter(learning_unit_year=attribution.learning_unit_year) \
                .filter(tutor=attribution.tutor)
            for a_attribution in attributions:
                a_attribution.score_responsible = True
                a_attribution.save()
    url = reverse('scores_responsible_search')
    return HttpResponseRedirect(url + "?course_code=%s&learning_unit_title=%s&tutor=%s&scores_responsible=%s"
                                % (request.POST.get('course_code'),
                                   request.POST.get('learning_unit_title'),
                                   request.POST.get('tutor'),
                                   request.POST.get('scores_responsible')))
