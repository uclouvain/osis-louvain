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
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from attribution.views.perms import tutor_can_view_educational_information
from base.business.learning_units.perms import is_eligible_to_update_learning_unit_pedagogy, \
    find_educational_information_submission_dates_of_learning_unit_year, can_user_edit_educational_information
from base.models.learning_unit_year import find_learning_unit_years_by_academic_year_tutor_attributions
from attribution.models.attribution import find_all_summary_responsibles_by_learning_unit_years

from base.models import academic_year, entity_calendar
from base.models.enums import academic_calendar_type
from base.models.learning_unit_year import LearningUnitYear
from base.models.tutor import Tutor
from base.views import layout
from base.views import teaching_material
from base.views.learning_units.pedagogy.update import edit_learning_unit_pedagogy, \
    update_mobility_modality_view
from base.views.learning_units.pedagogy.read import read_learning_unit_pedagogy
from base.views.learning_units.perms import PermissionDecorator


@login_required
def list_my_attributions_summary_editable(request):
    tutor = get_object_or_404(Tutor, person__user=request.user)
    current_ac = academic_year.current_academic_year()
    learning_unit_years = find_learning_unit_years_by_academic_year_tutor_attributions(
        academic_year=current_ac.next(),
        tutor=tutor
    )
    score_responsibles = find_all_summary_responsibles_by_learning_unit_years(learning_unit_years)

    entity_calendars = entity_calendar.build_calendar_by_entities(
        ac_year=current_ac,
        reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION
    )
    errors = (can_user_edit_educational_information(user=tutor.person.user, learning_unit_year_id=luy.id)
              for luy in learning_unit_years)
    context = {
        'learning_unit_years_with_errors': zip(learning_unit_years, errors),
        'entity_calendars': entity_calendars,
        'score_responsibles': score_responsibles,
    }
    return layout.render(request, 'manage_my_courses/list_my_courses_summary_editable.html', context)


@login_required
@tutor_can_view_educational_information
def view_educational_information(request, learning_unit_year_id):
    context = {
        'submission_dates': find_educational_information_submission_dates_of_learning_unit_year(
                learning_unit_year_id),
        'create_teaching_material_urlname': 'tutor_teaching_material_create',
        'update_teaching_material_urlname': 'tutor_teaching_material_edit',
        'delete_teaching_material_urlname': 'tutor_teaching_material_delete',
        'update_mobility_modality_urlname': 'tutor_mobility_modality_update'
    }
    template = 'manage_my_courses/educational_information.html'
    return read_learning_unit_pedagogy(request, learning_unit_year_id, context, template)


@login_required
@PermissionDecorator(is_eligible_to_update_learning_unit_pedagogy, "learning_unit_year_id", LearningUnitYear)
def edit_educational_information(request, learning_unit_year_id):
    redirect_url = reverse(view_educational_information, kwargs={'learning_unit_year_id': learning_unit_year_id})
    return edit_learning_unit_pedagogy(request, learning_unit_year_id, redirect_url)


@login_required
@require_http_methods(['POST', 'GET'])
@PermissionDecorator(is_eligible_to_update_learning_unit_pedagogy, "learning_unit_year_id", LearningUnitYear)
def create_teaching_material(request, learning_unit_year_id):
    success_url = reverse(view_educational_information, kwargs={'learning_unit_year_id': learning_unit_year_id})
    return teaching_material.create_view(request, learning_unit_year_id, success_url)


@login_required
@require_http_methods(['POST', 'GET'])
@PermissionDecorator(is_eligible_to_update_learning_unit_pedagogy, "learning_unit_year_id", LearningUnitYear)
def update_teaching_material(request, learning_unit_year_id, teaching_material_id):
    success_url = reverse(view_educational_information, kwargs={'learning_unit_year_id': learning_unit_year_id})
    return teaching_material.update_view(request, learning_unit_year_id, teaching_material_id, success_url)


@login_required
@require_http_methods(['POST', 'GET'])
@PermissionDecorator(is_eligible_to_update_learning_unit_pedagogy, "learning_unit_year_id", LearningUnitYear)
def delete_teaching_material(request, learning_unit_year_id, teaching_material_id):
    success_url = reverse(view_educational_information, kwargs={'learning_unit_year_id': learning_unit_year_id})
    return teaching_material.delete_view(request, learning_unit_year_id, teaching_material_id, success_url)


@login_required
@require_http_methods(['POST', 'GET'])
@PermissionDecorator(is_eligible_to_update_learning_unit_pedagogy, "learning_unit_year_id", LearningUnitYear)
def update_mobility_modality(request, learning_unit_year_id):
    success_url = reverse(view_educational_information, kwargs={'learning_unit_year_id': learning_unit_year_id})
    return update_mobility_modality_view(request, learning_unit_year_id, success_url)
