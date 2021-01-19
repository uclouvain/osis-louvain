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
import itertools
from typing import Iterable

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

from attribution.views.perms import tutor_can_view_educational_information
from base.business.learning_units.perms import is_eligible_to_update_learning_unit_pedagogy, \
    find_educational_information_submission_dates_of_learning_unit_year, CanUserEditEducationalInformation, \
    find_educational_information_force_majeure_submission_dates_of_learning_unit_year, \
    is_eligible_to_update_learning_unit_pedagogy_force_majeure_section, CanUserEditEducationalInformationForceMajeure
from base.models import entity_calendar
from base.models.academic_year import AcademicYear
from base.models.enums import academic_calendar_type
from base.models.learning_unit_year import LearningUnitYear
from base.models.tutor import Tutor
from base.views import teaching_material
from base.views.learning_unit import get_specifications_context, get_achievements_group_by_language, \
    get_languages_settings
from base.views.learning_units.pedagogy.read import read_learning_unit_pedagogy
from base.views.learning_units.pedagogy.update import edit_learning_unit_pedagogy, \
    post_method_edit_force_majeure_pedagogy
from base.views.learning_units.perms import PermissionDecorator
from education_group.templatetags.academic_year_display import display_as_academic_year
from learning_unit.calendar.learning_unit_force_majeur_summary_edition import \
    LearningUnitForceMajeurSummaryEditionCalendar
from learning_unit.calendar.learning_unit_summary_edition_calendar import LearningUnitSummaryEditionCalendar


@login_required
def list_my_attributions_summary_editable(request):
    tutor = get_object_or_404(Tutor, person__user=request.user)

    summary_edition_calendar = LearningUnitSummaryEditionCalendar()
    summary_edition_academic_events = summary_edition_calendar.get_opened_academic_events()
    if summary_edition_academic_events:
        main_summary_edition_academic_event = summary_edition_academic_events[0]
    else:
        main_summary_edition_academic_event = summary_edition_calendar.get_previous_academic_event()
        messages.add_message(
            request,
            messages.INFO,
            _('For the academic year %(data_year)s, the summary edition period ended on %(end_date)s.') % {
                "data_year": display_as_academic_year(main_summary_edition_academic_event.authorized_target_year),
                "end_date": main_summary_edition_academic_event.end_date.strftime('%d/%m/%Y'),
            }
        )
        next_academic_event = summary_edition_calendar.get_next_academic_event()
        if next_academic_event:
            messages.add_message(
                request,
                messages.INFO,
                _('For the academic year %(data_year)s, the summary edition period will open on %(start_date)s.') % {
                    "data_year": display_as_academic_year(next_academic_event.authorized_target_year),
                    "start_date": next_academic_event.start_date.strftime('%d/%m/%Y'),
                }
            )

    force_majeur_summary_edition_calendar = LearningUnitForceMajeurSummaryEditionCalendar()
    force_majeur_summary_edition_academic_events = force_majeur_summary_edition_calendar.get_opened_academic_events()
    if force_majeur_summary_edition_academic_events:
        force_majeure_academic_event = force_majeur_summary_edition_academic_events[0]
        messages.add_message(
            request,
            messages.WARNING,
            _('Force majeure case : Some fields of the description fiche can be edited from %(start_date)s '
              'to %(end_date)s.') % {
                "start_date": force_majeure_academic_event.start_date.strftime('%d/%m/%Y'),
                "end_date": force_majeure_academic_event.end_date.strftime('%d/%m/%Y'),
            }
        )
    else:
        force_majeure_academic_event = force_majeur_summary_edition_calendar.get_academic_event(
            target_year=main_summary_edition_academic_event.authorized_target_year
        )

    if not main_summary_edition_academic_event.is_open_now() and force_majeure_academic_event.is_open_now():
        year_displayed = force_majeure_academic_event.authorized_target_year
    else:
        year_displayed = main_summary_edition_academic_event.authorized_target_year
    academic_year = AcademicYear.objects.get(year=year_displayed)
    learning_unit_years_qs = LearningUnitYear.objects_with_container.filter(
        academic_year=academic_year,
        attribution__tutor=tutor,
    ).distinct().order_by('academic_year__year', 'acronym')

    entity_calendars = entity_calendar.build_calendar_by_entities(
        ac_year=academic_year,
        reference=academic_calendar_type.SUMMARY_COURSE_SUBMISSION
    )
    errors = (CanUserEditEducationalInformation(
        user=tutor.person.user, learning_unit_year_id=luy.id) for luy in learning_unit_years_qs)
    errors_force_majeure = (CanUserEditEducationalInformationForceMajeure(
        user=tutor.person.user, learning_unit_year_id=luy.id) for luy in learning_unit_years_qs)

    context = {
        'learning_unit_years_with_errors': list(zip(learning_unit_years_qs, errors, errors_force_majeure)),
        'entity_calendars': entity_calendars,
        'event_perm_desc_fiche_open': bool(summary_edition_calendar.get_target_years_opened()),
        'event_perm_force_majeure_open': bool(force_majeur_summary_edition_calendar.get_target_years_opened()),
        'event_perm_force_majeure_start_date': force_majeure_academic_event.start_date if force_majeure_academic_event
        else None,
        'event_perm_force_majeure_end_date': force_majeure_academic_event.end_date if force_majeure_academic_event
        else None
    }
    return render(request, 'manage_my_courses/list_my_courses_summary_editable.html', context)


@login_required
@tutor_can_view_educational_information
def view_educational_information(request, learning_unit_year_id):
    context = {
        'submission_dates': find_educational_information_submission_dates_of_learning_unit_year(
            learning_unit_year_id),
        'force_majeure_submission_dates':
            find_educational_information_force_majeure_submission_dates_of_learning_unit_year(learning_unit_year_id),
        'create_teaching_material_urlname': 'tutor_teaching_material_create',
        'update_teaching_material_urlname': 'tutor_teaching_material_edit',
        'delete_teaching_material_urlname': 'tutor_teaching_material_delete',
        'update_mobility_modality_urlname': 'tutor_mobility_modality_update'
    }
    template = 'manage_my_courses/educational_information.html'
    query_set = LearningUnitYear.objects.all().select_related('learning_unit', 'learning_container_year')
    learning_unit_year = get_object_or_404(query_set, pk=learning_unit_year_id)
    context.update(get_specifications_context(learning_unit_year, request))

    context["achievements"] = _fetch_achievements_by_language(learning_unit_year)

    context.update(get_languages_settings())
    context['div_class'] = 'collapse'
    return read_learning_unit_pedagogy(request, learning_unit_year_id, context, template)


def _fetch_achievements_by_language(learning_unit_year: LearningUnitYear) -> Iterable:
    fr_achievement_code = "achievements_FR"
    en_achievement_code = "achievements_EN"
    achievements = get_achievements_group_by_language(learning_unit_year)
    return itertools.zip_longest(achievements.get(fr_achievement_code, []), achievements.get(en_achievement_code, []))


@login_required
@PermissionDecorator(is_eligible_to_update_learning_unit_pedagogy, "learning_unit_year_id", LearningUnitYear)
def edit_educational_information(request, learning_unit_year_id):
    return edit_learning_unit_pedagogy(request, learning_unit_year_id)


@login_required
@PermissionDecorator(is_eligible_to_update_learning_unit_pedagogy_force_majeure_section, "learning_unit_year_id",
                     LearningUnitYear)
def edit_educational_information_force_majeure(request, learning_unit_year_id):
    if request.method == 'POST':
        return post_method_edit_force_majeure_pedagogy(request)
    return edit_learning_unit_pedagogy(request, learning_unit_year_id)


@login_required
@require_http_methods(['POST', 'GET'])
@PermissionDecorator(is_eligible_to_update_learning_unit_pedagogy, "learning_unit_year_id", LearningUnitYear)
def create_teaching_material(request, learning_unit_year_id):
    return teaching_material.create_view(request, learning_unit_year_id)


@login_required
@require_http_methods(['POST', 'GET'])
@PermissionDecorator(is_eligible_to_update_learning_unit_pedagogy, "learning_unit_year_id", LearningUnitYear)
def update_teaching_material(request, learning_unit_year_id, teaching_material_id):
    return teaching_material.update_view(request, learning_unit_year_id, teaching_material_id)


@login_required
@require_http_methods(['POST', 'GET'])
@PermissionDecorator(is_eligible_to_update_learning_unit_pedagogy, "learning_unit_year_id", LearningUnitYear)
def delete_teaching_material(request, learning_unit_year_id, teaching_material_id):
    return teaching_material.delete_view(request, learning_unit_year_id, teaching_material_id)
