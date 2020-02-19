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
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.http import require_http_methods

from base.business.learning_units import perms
from base.business.learning_units.pedagogy import delete_teaching_material
from base.forms.learning_unit_pedagogy import TeachingMaterialModelForm
from base.models.learning_unit_year import LearningUnitYear
from base.models.teaching_material import TeachingMaterial
from base.views.common import display_success_messages
from base.views.learning_units.pedagogy import update as update_pedagogy
from base.views.learning_units.perms import PermissionDecorator


@login_required
@require_http_methods(['POST', 'GET'])
@PermissionDecorator(perms.is_eligible_to_update_learning_unit_pedagogy, "learning_unit_year_id", LearningUnitYear)
def create(request, learning_unit_year_id):
    return create_view(request, learning_unit_year_id)


@login_required
@require_http_methods(['POST', 'GET'])
@PermissionDecorator(perms.is_eligible_to_update_learning_unit_pedagogy, "learning_unit_year_id", LearningUnitYear)
def update(request, learning_unit_year_id, teaching_material_id):
    return update_view(request, learning_unit_year_id, teaching_material_id)


@login_required
@require_http_methods(['POST', 'GET'])
@PermissionDecorator(perms.is_eligible_to_update_learning_unit_pedagogy, "learning_unit_year_id", LearningUnitYear)
def delete(request, learning_unit_year_id, teaching_material_id):
    return delete_view(request, learning_unit_year_id, teaching_material_id)


def create_view(request, learning_unit_year_id):
    learning_unit_yr = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)
    form = TeachingMaterialModelForm(request.POST or None)
    if form.is_valid():
        return _save_and_return_response(request, form, learning_unit_yr)
    return render(request, "learning_unit/teaching_material/modal_edit.html", {'form': form})


def update_view(request, learning_unit_year_id, teaching_material_id):
    teach_material = get_object_or_404(TeachingMaterial, pk=teaching_material_id,
                                       learning_unit_year_id=learning_unit_year_id)
    form = TeachingMaterialModelForm(request.POST or None, instance=teach_material)
    if form.is_valid():
        return _save_and_return_response(request, form, teach_material.learning_unit_year)
    return render(request, "learning_unit/teaching_material/modal_edit.html", {'form': form})


def delete_view(request, learning_unit_year_id, teaching_material_id):
    learning_unit_yr = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)
    teach_material = get_object_or_404(TeachingMaterial, pk=teaching_material_id,
                                       learning_unit_year_id=learning_unit_year_id)
    if request.method == 'POST':
        last_luy_reported = teach_material.learning_unit_year.find_gt_learning_units_year().last()
        delete_teaching_material(teach_material)
        display_success_messages(request, update_pedagogy.build_success_message(last_luy_reported, learning_unit_yr))
        return JsonResponse({})
    return render(request, "learning_unit/teaching_material/modal_delete.html", {})


def _save_and_return_response(request, form, learning_unit_year):
    form.save(learning_unit_year=learning_unit_year)
    last_luy_reported = learning_unit_year.find_gt_learning_units_year().last()
    display_success_messages(request, update_pedagogy.build_success_message(last_luy_reported, learning_unit_year))
    return JsonResponse({})
