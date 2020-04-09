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
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from base.business.learning_units.achievement import get_anchor_reference, DELETE, DOWN, UP, \
    AVAILABLE_ACTIONS
from base.forms.learning_achievement import LearningAchievementEditForm
from base.models.learning_achievement import LearningAchievement, find_learning_unit_achievement
from base.models.learning_unit_year import LearningUnitYear
from base.views.common import display_success_messages
from base.views.learning_unit import learning_unit_specifications, build_success_message
from base.views.learning_units import perms
from osis_common.utils.models import get_object_or_none
from reference.models.language import EN_CODE_LANGUAGE, FR_CODE_LANGUAGE


def operation(request, learning_achievement_id, operation_str):
    achievement_fr = get_object_or_404(
        LearningAchievement.objects.select_related('learning_unit_year__academic_year'),
        pk=learning_achievement_id
    )
    lu_yr_id = achievement_fr.learning_unit_year.id

    achievement_en = find_learning_unit_achievement(
        achievement_fr.consistency_id,
        achievement_fr.learning_unit_year,
        EN_CODE_LANGUAGE,
        achievement_fr.order
    )
    anchor = get_anchor_reference(operation_str, achievement_fr)
    filtered_achievements = list(filter(None, [achievement_fr, achievement_en]))
    last_academic_year = execute_operation(filtered_achievements, operation_str)
    if last_academic_year and last_academic_year.year <= achievement_fr.learning_unit_year.academic_year.year:
        display_success_messages(
            request, build_success_message(None, lu_yr_id, False)
        )
    else:
        display_success_messages(
            request, build_success_message(last_academic_year, lu_yr_id, True)
        )

    return HttpResponseRedirect(reverse(learning_unit_specifications,
                                        kwargs={'learning_unit_year_id': lu_yr_id}) + anchor)


def execute_operation(achievements, operation_str):
    last_academic_year = None
    for an_achievement in achievements:
        curr_order = an_achievement.order
        next_luy = an_achievement.learning_unit_year
        neighbouring_achievements = _get_neighbouring_achievements(an_achievement)
        func = getattr(an_achievement, operation_str)
        func()
        if not next_luy.is_past():
            last_academic_year = _postpone_operation(neighbouring_achievements, next_luy, operation_str, curr_order)
    return last_academic_year


def _get_neighbouring_achievements(achievement):
    kwargs = {'learning_unit_year': achievement.learning_unit_year, 'language': achievement.language}
    previous_achievement = get_object_or_none(LearningAchievement, order=achievement.order - 1, **kwargs)
    next_achievement = get_object_or_none(LearningAchievement, order=achievement.order + 1, **kwargs)
    return previous_achievement, achievement, next_achievement


def _postpone_operation(neighbouring_achievements, next_luy, operation_str, curr_order):
    _, achievement, _ = neighbouring_achievements
    while next_luy.get_learning_unit_next_year():
        current_luy = next_luy
        next_luy = next_luy.get_learning_unit_next_year()
        next_luy_achievement = get_object_or_none(
            LearningAchievement,
            learning_unit_year=next_luy,
            consistency_id=achievement.consistency_id,
            language=achievement.language
        )
        if next_luy_achievement and \
                _operation_is_postponable(next_luy_achievement, neighbouring_achievements, operation_str, curr_order):
            getattr(next_luy_achievement, operation_str)()
        else:
            return current_luy.academic_year
    return next_luy.academic_year


def _operation_is_postponable(next_luy_achievement, neighbouring_achievements, operation_str, current_order):
    # order operation is postponable only if neighbouring achievements order is the same in future years
    previous_achievement, achievement, next_achievement = neighbouring_achievements
    if operation_str in [DOWN, UP]:
        neighbour_current_order = current_order + 1 if operation_str == DOWN else current_order - 1
        neighbour_achievement = next_achievement if operation_str == DOWN else previous_achievement
        return _has_same_order_in_future(achievement, current_order, next_luy_achievement) and \
            _has_same_order_in_future(neighbour_achievement, neighbour_current_order, next_luy_achievement)
    return True


def _has_same_order_in_future(achievement, current_order, next_luy_achievement):
    return LearningAchievement.objects.filter(
        consistency_id=achievement.consistency_id,
        learning_unit_year=next_luy_achievement.learning_unit_year,
        language=achievement.language,
        order=current_order
    ).exists()


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@require_http_methods(['POST'])
@perms.can_update_learning_achievement
def management(request, learning_unit_year_id):
    return operation(request, request.POST.get('achievement_id'), get_action(request))


def get_action(request):
    action = request.POST.get('action')
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
    form = LearningAchievementEditForm(
        request.POST or None,
        luy=learning_unit_year,
        code=learning_achievement.code_name,
        consistency_id=learning_achievement.consistency_id,
        order=learning_achievement.order
    )

    if form.is_valid():
        return _save_and_redirect(request, form, learning_unit_year_id)

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
    form = LearningAchievementEditForm(
        request.POST or None,
        luy=learning_unit_yr,
        consistency_id=_get_last_consistency_id(learning_unit_yr.learning_unit)+1
    )
    if form.is_valid():
        return _save_and_redirect(request, form, learning_unit_year_id)

    context = {'learning_unit_year': learning_unit_yr,
               'learning_achievement': learning_achievement_fr,
               'form': form,
               'language_code': a_language_code,
               'create': True}

    return render(request, "learning_unit/achievement_edit.html", context)


def _get_last_consistency_id(learning_unit):
    try:
        return LearningAchievement.objects.filter(
            learning_unit_year__learning_unit=learning_unit
        ).order_by("consistency_id").last().consistency_id
    except AttributeError:
        return 0


def _save_and_redirect(request, form, learning_unit_year_id):
    achievement, last_academic_year = form.save()
    display_success_messages(
        request,
        build_success_message(
            last_academic_year,
            learning_unit_year_id,
            form.postponement
        )
    )
    return HttpResponse()


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@require_http_methods(['POST', 'GET'])
@perms.can_update_learning_achievement
def create_first(request, learning_unit_year_id):
    learning_unit_yr = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)
    form = LearningAchievementEditForm(
        request.POST or None,
        luy=learning_unit_yr,
        consistency_id=_get_last_consistency_id(learning_unit_yr.learning_unit)+1
    )
    if form.is_valid():
        return _save_and_redirect(request, form, learning_unit_year_id)

    context = {
        'learning_unit_year': learning_unit_yr,
        'form': form,
        'language_code': FR_CODE_LANGUAGE
    }

    return render(request, "learning_unit/achievement_edit.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@require_http_methods(['GET'])
@perms.can_update_learning_achievement
def check_code(request, learning_unit_year_id):
    code = request.GET['code']
    luy = LearningUnitYear.objects.get(id=learning_unit_year_id)
    learning_achievement = LearningAchievement.objects.filter(
        learning_unit_year__learning_unit__learningunityear__id=learning_unit_year_id,
        code_name=code
    ).exclude(learning_unit_year__academic_year__year__lte=luy.academic_year.year).first()
    academic_year = learning_achievement.learning_unit_year.academic_year.name if learning_achievement else None
    return JsonResponse(data={'accept_postponement': learning_achievement is None, 'academic_year': academic_year})
