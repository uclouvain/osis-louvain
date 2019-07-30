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
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from base.business.learning_units.achievement import get_code_name, get_anchor_reference, DELETE, DOWN, UP, \
    AVAILABLE_ACTIONS, HTML_ANCHOR
from base.forms.learning_achievement import LearningAchievementEditForm
from base.models.learning_achievement import LearningAchievement, find_learning_unit_achievement
from base.models.learning_unit_year import LearningUnitYear
from base.views.learning_unit import learning_unit_specifications
from base.views.learning_units import perms
from reference.models import language
from reference.models.language import EN_CODE_LANGUAGE, FR_CODE_LANGUAGE


def operation(learning_achievement_id, operation_str):
    achievement_fr = get_object_or_404(LearningAchievement, pk=learning_achievement_id)
    lu_yr_id = achievement_fr.learning_unit_year.id

    achievement_en = find_learning_unit_achievement(achievement_fr.learning_unit_year,
                                                    EN_CODE_LANGUAGE,
                                                    achievement_fr.order)
    anchor = get_anchor_reference(operation_str, achievement_fr)
    execute_operation(achievement_fr, operation_str)
    execute_operation(achievement_en, operation_str)

    return HttpResponseRedirect(reverse(learning_unit_specifications,
                                        kwargs={'learning_unit_year_id': lu_yr_id}) + anchor)


def execute_operation(an_achievement, operation_str):
    if an_achievement:
        func = getattr(an_achievement, operation_str)
        func()


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@require_http_methods(['POST'])
@perms.can_update_learning_achievement
def management(request, learning_unit_year_id):
    return operation(request.POST.get('achievement_id'), get_action(request))


def get_action(request):
    action = request.POST.get('action', None)
    if action not in AVAILABLE_ACTIONS:
        raise AttributeError('Action should be {}, {} or {}'.format(DELETE, UP, DOWN))
    return action


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@require_http_methods(["GET", "POST"])
@perms.can_update_learning_achievement
def update(request, learning_unit_year_id, learning_achievement_id):
    learning_achievement = get_object_or_404(LearningAchievement, pk=learning_achievement_id)
    learning_unit_year = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)

    form = LearningAchievementEditForm(request.POST or None, instance=learning_achievement)
    if form.is_valid():
        return _save_and_redirect(form, learning_unit_year_id)

    context = {'learning_unit_year': learning_unit_year,
               'learning_achievement': learning_achievement,
               'form': form}

    return render(request, "learning_unit/achievement_edit.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@require_http_methods(['POST', 'GET'])
@perms.can_update_learning_achievement
def create(request, learning_unit_year_id, learning_achievement_id):
    learning_unit_yr = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)
    a_language_code = request.GET.get('language_code', None)
    learning_achievement_fr = get_object_or_404(LearningAchievement, pk=learning_achievement_id)

    form = LearningAchievementEditForm(request.POST or None,
                                       initial={'learning_unit_year': learning_unit_yr,
                                                'language_code': a_language_code,
                                                'code_name': get_code_name(learning_achievement_fr,
                                                                           a_language_code)})

    if form.is_valid():
        return _save_and_redirect(form, learning_unit_year_id)

    context = {'learning_unit_year': learning_unit_yr,
               'learning_achievement': learning_achievement_fr,
               'form': form,
               'language_code': a_language_code,
               'create': True}

    return render(request, "learning_unit/achievement_edit.html", context)


def _save_and_redirect(form, learning_unit_year_id):
    achievement = form.save()
    return HttpResponseRedirect(
        reverse(learning_unit_specifications, kwargs={'learning_unit_year_id': learning_unit_year_id})
        + "{}{}".format(HTML_ANCHOR, achievement.id)
    )


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@require_http_methods(['POST', 'GET'])
@perms.can_update_learning_achievement
def create_first(request, learning_unit_year_id):
    learning_unit_yr = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)
    form = LearningAchievementEditForm(request.POST or None,
                                       initial={'language': language.find_by_code(FR_CODE_LANGUAGE),
                                                'learning_unit_year': learning_unit_yr})

    if form.is_valid():
        return _save_and_redirect(form, learning_unit_year_id)

    context = {'learning_unit_year': learning_unit_yr,
               'form': form,
               'language_code': FR_CODE_LANGUAGE}

    return render(request, "learning_unit/achievement_edit.html", context)
