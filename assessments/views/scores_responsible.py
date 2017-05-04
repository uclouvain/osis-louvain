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
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from attribution import models as mdl_attr
from attribution.models.attribution import Attribution
from base.models import entity_manager
from base.models.learning_unit_year import LearningUnitYear
from base.views import layout


def is_faculty_admin(user):
    a_faculty_administrator = entity_manager.find_entity_manager_by_user(user)
    return a_faculty_administrator if a_faculty_administrator else False


@login_required
@user_passes_test(is_faculty_admin)
def scores_responsible(request):
    a_faculty_administrator = entity_manager.find_entity_manager_by_user(request.user)
    all_tutors, attributions, attributions_list, responsibles_list = find_data_table(request,
                                                                                     a_faculty_administrator.structure)
    dict_attribution = create_dictionary(attributions)
    return layout.render(request, 'scores_responsible.html', {"all_tutors": all_tutors,
                                                              "attributions_list": attributions_list,
                                                              "dict_attribution": dict_attribution,
                                                              "attributions": attributions,
                                                              "responsibles_list": responsibles_list})


@login_required
@user_passes_test(is_faculty_admin)
def scores_responsible_search(request):
    a_faculty_administrator = entity_manager.find_entity_manager_by_user(request.user)
    attributions_searched = mdl_attr.attribution.search_scores_responsible(
        structure=a_faculty_administrator.structure,
        learning_unit_title=request.GET['learning_unit_title'],
        course_code=request.GET['course_code'],
        entity=request.GET['entity'],
        professor=request.GET['professor'],
        scores_responsible=request.GET['scores_responsible'])
    all_tutors, attributions, attributions_list, responsibles_list = find_data_table(request,
                                                                                     a_faculty_administrator.structure)
    dict_attribution = create_dictionary(attributions_searched)
    return layout.render(request, 'scores_responsible.html', {"all_tutors": all_tutors,
                                                              "attributions_list": attributions_list,
                                                              "dict_attribution": dict_attribution,
                                                              "attributions": attributions,
                                                              "responsibles_list": responsibles_list})


def create_dictionary(attributions):
    dict_attribution = dict()
    for attribution in attributions:
        tutor_number = mdl_attr.attribution.find_tutor_number(attribution)
        responsible = mdl_attr.attribution.find_responsible(attribution.learning_unit_year)
        dict_attribution.update({attribution: [attribution.learning_unit_year.id,
                                               attribution.learning_unit_year.structure.acronym,
                                               attribution.learning_unit_year.acronym,
                                               attribution.learning_unit_year.title,
                                               tutor_number, responsible]})
    return dict_attribution


def find_data_table(request, structure):
    a_faculty_administrator = entity_manager.find_entity_manager_by_user(request.user)
    attributions = mdl_attr.attribution.find_attributions(structure).distinct("learning_unit_year")
    responsibles_list = mdl_attr.attribution.find_responsible_distinct(structure)
    attributions_list = mdl_attr.attribution.find_attribution_distinct(structure)
    all_tutors = mdl_attr.attribution.find_all_tutor(a_faculty_administrator.structure).distinct("tutor")
    return all_tutors, attributions, attributions_list, responsibles_list


def scores_responsible_list(request):
    list_course_code = request.GET['course_code']
    return list_course_code


@login_required
@user_passes_test(is_faculty_admin)
def scores_responsible_management(request, pk):
    learning_unit_year = get_object_or_404(LearningUnitYear, pk=pk)
    a_faculty_administrator = entity_manager.find_entity_manager_by_user(request.user)
    professors = mdl_attr.attribution.find_all_responsable_by_learning_unit_year(a_faculty_administrator.structure,
                                                                                 learning_unit_year)
    attributions = mdl_attr.attribution.find_all_tutor_by_learning_unit_year(learning_unit_year)
    return layout.render(request, 'scores_responsible_edit.html',
                         {'learning_unit_year': learning_unit_year,
                          'professors': professors,
                          'attributions': attributions})


@login_required
@user_passes_test(is_faculty_admin)
def scores_responsible_delete(request, pk):
    attribution = get_object_or_404(Attribution, pk=pk)
    attribution.score_responsible = False
    attribution.save()
    return redirect('scores_responsible_management', pk=attribution.learning_unit_year.pk)


@login_required
@user_passes_test(is_faculty_admin)
def scores_responsible_add(request):
    attribution = get_object_or_404(Attribution, pk=request.GET['professor'])
    attribution.score_responsible = True
    attribution.save()
    return redirect('scores_responsible_management', pk=attribution.learning_unit_year.pk)
