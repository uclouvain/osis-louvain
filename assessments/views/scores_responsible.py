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
from django.contrib.auth.mixins import PermissionRequiredMixin, LoginRequiredMixin
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django_filters.views import FilterView

from assessments.api.serializers.scores_responsible import ScoresResponsibleListSerializer
from assessments.forms.scores_responsible import ScoresResponsibleFilter
from attribution import models as mdl_attr
from attribution.business.score_responsible import get_attributions_data
from attribution.models.attribution import Attribution
from base import models as mdl_base
from base.models.learning_unit_year import LearningUnitYear
from base.utils.cache import CacheFilterMixin


class ScoresResponsibleSearch(LoginRequiredMixin, PermissionRequiredMixin, CacheFilterMixin, FilterView):
    model = LearningUnitYear
    paginate_by = 20
    template_name = "scores_responsible/list.html"

    filterset_class = ScoresResponsibleFilter
    permission_required = 'assessments.view_scoresresponsible'

    def get_filterset_kwargs(self, filterset_class):
        return {
            **super().get_filterset_kwargs(filterset_class),
            'academic_year': mdl_base.academic_year.current_academic_year()
        }

    def render_to_response(self, context, **response_kwargs):
        if self.request.is_ajax():
            serializer = ScoresResponsibleListSerializer(context['object_list'], many=True)
            return JsonResponse({'object_list': serializer.data})
        return super().render_to_response(context, **response_kwargs)


@login_required
@permission_required('assessments.change_scoresresponsible', raise_exception=True)
def scores_responsible_management(request):
    context = {
        'course_code': request.GET.get('course_code'),
        'learning_unit_title': request.GET.get('learning_unit_title'),
        'tutor': request.GET.get('tutor'),
        'scores_responsible': request.GET.get('scores_responsible')
    }
    learning_unit_year_id = request.GET.get('learning_unit_year').strip('learning_unit_year_')
    attributions_data = get_attributions_data(request.user, learning_unit_year_id, '-score_responsible')
    context.update(attributions_data)
    return render(request, 'scores_responsible_edit.html', context)


@login_required
@permission_required('assessments.change_scoresresponsible', raise_exception=True)
def scores_responsible_add(request, pk):
    if request.POST.get('action') == "add":
        mdl_attr.attribution.clear_scores_responsible_by_learning_unit_year(pk)
        if request.POST.get('attribution'):
            attribution_id = request.POST.get('attribution').strip('attribution_')
            attribution = Attribution.objects.get(pk=attribution_id)
            attributions = mdl_attr.attribution.Attribution.objects \
                .filter(learning_unit_year=attribution.learning_unit_year) \
                .filter(tutor=attribution.tutor)
            for a_attribution in attributions:
                a_attribution.score_responsible = True
                a_attribution.save()
    return HttpResponseRedirect(reverse('scores_responsible_list'))
