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

import re

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.db import IntegrityError
from django.db.models import BLANK_CHOICE_DASH
from django.forms import model_to_dict
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.http import QueryDict
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods, require_POST, require_GET

from attribution.business import attribution_charge_new
from base import models as mdl
from base import models as mdl_base
from base.business import learning_unit_deletion, learning_unit_year_volumes, learning_unit_year_with_context
from base.business.learning_unit import create_learning_unit, create_learning_unit_structure, get_cms_label_data, \
    extract_volumes_from_data, get_same_container_year_components, get_components_identification, show_subtype, \
    get_organization_from_learning_unit_year, get_campus_from_learning_unit_year, \
    get_all_attributions, SIMPLE_SEARCH, SERVICE_COURSES_SEARCH, create_xls, is_summary_submission_opened, \
    find_language_in_settings, \
    initialize_learning_unit_pedagogy_form, compute_max_academic_year_adjournment, \
    create_learning_unit_partim_structure, can_access_summary, get_last_academic_years, CMS_LABEL_SPECIFICATIONS, \
    CMS_LABEL_PEDAGOGY, CMS_LABEL_SUMMARY
from base.business.learning_units import perms as business_perms
from base.forms.common import TooManyResultsException
from base.forms.learning_class import LearningClassEditForm
from base.forms.learning_unit_component import LearningUnitComponentEditForm
from base.forms.learning_unit_create import CreateLearningUnitYearForm, CreatePartimForm, \
    PARTIM_FORM_READ_ONLY_FIELD
from base.forms.learning_unit_pedagogy import LearningUnitPedagogyEditForm
from base.forms.learning_unit_specifications import LearningUnitSpecificationsForm, LearningUnitSpecificationsEditForm
from base.forms.learning_units import LearningUnitYearForm
from base.models import proposal_learning_unit, entity_container_year
from base.models.enums import learning_container_year_types, learning_unit_year_subtypes
from base.models.enums.learning_unit_year_subtypes import FULL, PARTIM
from base.models.learning_container import LearningContainer
from base.models.learning_unit import LEARNING_UNIT_ACRONYM_REGEX_ALL, LEARNING_UNIT_ACRONYM_REGEX_FULL
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.views.common import display_error_messages, display_success_messages
from base.views.learning_units import perms
from cms.models import text_label
from reference.models import language
from . import layout


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_units(request):
    return _learning_units_search(request, SIMPLE_SEARCH)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_units_service_course(request):
    return _learning_units_search(request, SERVICE_COURSES_SEARCH)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_identification(request, learning_unit_year_id):
    person = get_object_or_404(Person, user=request.user)
    context = get_learning_unit_identification_context(learning_unit_year_id, person)
    return layout.render(request, "learning_unit/identification.html", context)


def _get_common_context_learning_unit_year(learning_unit_year_id, person):
    learning_unit_year = mdl_base.learning_unit_year.get_by_id(learning_unit_year_id)
    is_person_linked_to_entity = business_perms. \
        is_person_linked_to_entity_in_charge_of_learning_unit(learning_unit_year, person)
    return {
        'learning_unit_year': learning_unit_year,
        'current_academic_year': mdl_base.academic_year.current_academic_year(),
        'is_person_linked_to_entity': is_person_linked_to_entity
    }


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_formations(request, learning_unit_year_id):
    context = _get_common_context_learning_unit_year(learning_unit_year_id,
                                                     get_object_or_404(Person, user=request.user))
    return layout.render(request, "learning_unit/formations.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_components(request, learning_unit_year_id):
    person = get_object_or_404(Person, user=request.user)
    context = _get_common_context_learning_unit_year(learning_unit_year_id, person)
    context['components'] = get_same_container_year_components(context['learning_unit_year'], True)
    context['tab_active'] = 'components'
    context['can_manage_volume'] = business_perms.is_eligible_for_modification(context["learning_unit_year"],
                                                                               person)
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/components.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def volumes_validation(request, learning_unit_year_id):
    volumes_encoded = extract_volumes_from_data(request.POST.dict())
    volumes_grouped_by_lunityear = learning_unit_year_volumes.get_volumes_grouped_by_lunityear(learning_unit_year_id,
                                                                                               volumes_encoded)
    return JsonResponse({
        'errors': learning_unit_year_volumes.validate(volumes_grouped_by_lunityear)
    })


@login_required
@permission_required('base.can_edit_learningunit', raise_exception=True)
@perms.can_perform_learning_unit_modification
def learning_unit_volumes_management(request, learning_unit_year_id):
    # FIXME : Use a formset instead !
    if request.method == 'POST':
        errors = _learning_unit_volumes_management_edit(request, learning_unit_year_id)

        if not errors:
            display_success_messages(request, _('success_modification_learning_unit'))
            return HttpResponseRedirect(reverse(learning_unit_components, args=[learning_unit_year_id]))

        display_error_messages(request, errors)

    context = _get_common_context_learning_unit_year(
        learning_unit_year_id,
        get_object_or_404(Person, user=request.user)
    )

    context['learning_units'] = learning_unit_year_with_context.get_with_context(
        learning_container_year_id=context['learning_unit_year'].learning_container_year_id
    )
    context['tab_active'] = 'components'
    context['experimental_phase'] = True

    return layout.render(request, "learning_unit/volumes_management.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_pedagogy(request, learning_unit_year_id):
    context = _get_common_context_learning_unit_year(learning_unit_year_id,
                                                     get_object_or_404(Person, user=request.user))
    learning_unit_year = context['learning_unit_year']
    user_language = mdl.person.get_user_interface_language(request.user)
    context['cms_labels_translated'] = get_cms_label_data(CMS_LABEL_PEDAGOGY, user_language)

    context['form_french'] = initialize_learning_unit_pedagogy_form(learning_unit_year, settings.LANGUAGE_CODE_FR)
    context['form_english'] = initialize_learning_unit_pedagogy_form(learning_unit_year, settings.LANGUAGE_CODE_EN)
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/pedagogy.html", context)


@login_required
@permission_required('base.can_edit_learningunit_pedagogy', raise_exception=True)
@require_http_methods(["GET", "POST"])
def learning_unit_pedagogy_edit(request, learning_unit_year_id):
    if request.method == 'POST':
        form = LearningUnitPedagogyEditForm(request.POST)
        if form.is_valid():
            form.save()
        return HttpResponseRedirect(reverse("learning_unit_pedagogy",
                                            kwargs={'learning_unit_year_id': learning_unit_year_id}))

    context = _get_common_context_learning_unit_year(learning_unit_year_id,
                                                     get_object_or_404(Person, user=request.user))
    label_name = request.GET.get('label')
    language = request.GET.get('language')
    text_lb = text_label.find_root_by_name(label_name)
    form = LearningUnitPedagogyEditForm(**{
        'learning_unit_year': context['learning_unit_year'],
        'language': language,
        'text_label': text_lb
    })
    form.load_initial()  # Load data from database
    context['form'] = form

    user_language = mdl.person.get_user_interface_language(request.user)
    context['text_label_translated'] = next((txt for txt in text_lb.translated_text_labels
                                             if txt.language == user_language), None)
    context['language_translated'] = find_language_in_settings(language)
    return layout.render(request, "learning_unit/pedagogy_edit.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_attributions(request, learning_unit_year_id):
    context = _get_common_context_learning_unit_year(learning_unit_year_id,
                                                     get_object_or_404(Person, user=request.user))
    context['attribution_charge_news'] = \
        attribution_charge_new.find_attribution_charge_new_by_learning_unit_year(
            learning_unit_year=learning_unit_year_id)
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/attributions.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_specifications(request, learning_unit_year_id):
    context = _get_common_context_learning_unit_year(learning_unit_year_id,
                                                     get_object_or_404(Person, user=request.user))
    learning_unit_year = context['learning_unit_year']

    user_language = mdl.person.get_user_interface_language(request.user)
    context['cms_labels_translated'] = get_cms_label_data(CMS_LABEL_SPECIFICATIONS, user_language)

    fr_language = find_language_in_settings(settings.LANGUAGE_CODE_FR)
    en_language = find_language_in_settings(settings.LANGUAGE_CODE_EN)

    context.update({
        'form_french': LearningUnitSpecificationsForm(learning_unit_year, fr_language),
        'form_english': LearningUnitSpecificationsForm(learning_unit_year, en_language)
    })
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/specifications.html", context)


@login_required
@permission_required('base.can_edit_learningunit_specification', raise_exception=True)
@require_http_methods(["GET", "POST"])
def learning_unit_specifications_edit(request, learning_unit_year_id):
    if request.method == 'POST':
        form = LearningUnitSpecificationsEditForm(request.POST)
        if form.is_valid():
            form.save()
        return HttpResponseRedirect(reverse("learning_unit_specifications",
                                            kwargs={'learning_unit_year_id': learning_unit_year_id}))

    context = _get_common_context_learning_unit_year(learning_unit_year_id,
                                                     get_object_or_404(Person, user=request.user))
    label_name = request.GET.get('label')
    text_lb = text_label.find_root_by_name(label_name)
    language = request.GET.get('language')
    form = LearningUnitSpecificationsEditForm(**{
        'learning_unit_year': context['learning_unit_year'],
        'language': language,
        'text_label': text_lb
    })
    form.load_initial()  # Load data from database
    context['form'] = form

    user_language = mdl.person.get_user_interface_language(request.user)
    context['text_label_translated'] = next((txt for txt in text_lb.translated_text_labels
                                             if txt.language == user_language), None)
    context['language_translated'] = find_language_in_settings(language)
    return layout.render(request, "learning_unit/specifications_edit.html", context)


@login_required
@permission_required('base.change_learningcomponentyear', raise_exception=True)
@require_http_methods(["GET", "POST"])
def learning_unit_component_edit(request, learning_unit_year_id):
    context = _get_common_context_learning_unit_year(learning_unit_year_id,
                                                     get_object_or_404(Person, user=request.user))
    learning_component_id = request.GET.get('learning_component_year_id')
    context['learning_component_year'] = mdl.learning_component_year.find_by_id(learning_component_id)

    if request.method == 'POST':
        form = LearningUnitComponentEditForm(request.POST,
                                             learning_unit_year=context['learning_unit_year'],
                                             instance=context['learning_component_year'])
        if form.is_valid():
            form.save()
        return HttpResponseRedirect(reverse(learning_unit_components,
                                            kwargs={'learning_unit_year_id': learning_unit_year_id}))

    form = LearningUnitComponentEditForm(learning_unit_year=context['learning_unit_year'],
                                         instance=context['learning_component_year'])
    form.load_initial()  # Load data from database
    context['form'] = form
    return layout.render(request, "learning_unit/component_edit.html", context)


@login_required
@permission_required('base.change_learningclassyear', raise_exception=True)
@require_http_methods(["GET", "POST"])
def learning_class_year_edit(request, learning_unit_year_id):
    context = _get_common_context_learning_unit_year(learning_unit_year_id,
                                                     get_object_or_404(Person, user=request.user))
    context.update(
        {'learning_class_year': mdl.learning_class_year.find_by_id(request.GET.get('learning_class_year_id')),
         'learning_component_year':
             mdl.learning_component_year.find_by_id(request.GET.get('learning_component_year_id'))})

    if request.method == 'POST':
        form = LearningClassEditForm(
            request.POST,
            instance=context['learning_class_year'],
            learning_unit_year=context['learning_unit_year'],
            learning_component_year=context['learning_component_year']
        )
        if form.is_valid():
            form.save()
        return HttpResponseRedirect(reverse("learning_unit_components",
                                            kwargs={'learning_unit_year_id': learning_unit_year_id}))

    form = LearningClassEditForm(
        instance=context['learning_class_year'],
        learning_unit_year=context['learning_unit_year'],
        learning_component_year=context['learning_component_year']
    )
    form.load_initial()  # Load data from database
    context['form'] = form
    return layout.render(request, "learning_unit/class_edit.html", context)


@login_required
@permission_required('base.can_create_learningunit', raise_exception=True)
def learning_unit_create(request, academic_year):
    person = get_object_or_404(Person, user=request.user)
    form = CreateLearningUnitYearForm(person, initial={'academic_year': academic_year,
                                                       'subtype': learning_unit_year_subtypes.FULL,
                                                       "container_type": BLANK_CHOICE_DASH,
                                                       'language': language.find_by_code('FR')})
    return layout.render(request, "learning_unit/learning_unit_form.html", {'form': form})


@login_required
@permission_required('base.can_create_learningunit', raise_exception=True)
@require_POST
def learning_unit_year_add(request):
    person = get_object_or_404(Person, user=request.user)
    form = CreateLearningUnitYearForm(person, request.POST)
    if form.is_valid():
        data = form.cleaned_data
        year = data['academic_year'].year
        status = data['status']
        additional_requirement_entity_1 = data.get('additional_requirement_entity_1')
        additional_requirement_entity_2 = data.get('additional_requirement_entity_2')
        allocation_entity_version = data.get('allocation_entity')
        requirement_entity_version = data.get('requirement_entity')
        campus = data.get('campus')

        new_learning_container = LearningContainer.objects.create()
        new_learning_unit = create_learning_unit(data, new_learning_container, year)
        while year <= compute_max_academic_year_adjournment():
            academic_year = mdl.academic_year.find_academic_year_by_year(year)
            luy_created = create_learning_unit_structure(additional_requirement_entity_1,
                                                         additional_requirement_entity_2, allocation_entity_version,
                                                         data, new_learning_container, new_learning_unit,
                                                         requirement_entity_version, status, academic_year, campus)
            _show_success_learning_unit_year_creation_message(request, luy_created)
            year += 1
        return redirect('learning_units')
    return layout.render(request, "learning_unit/learning_unit_form.html", {'form': form})


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def check_acronym(request, type):
    acronym = request.GET['acronym']
    academic_yr = mdl.academic_year.find_academic_year_by_id(request.GET['year_id'])
    existed_acronym = False
    existing_acronym = False
    first_using = ""
    last_using = ""
    learning_unit_year = mdl.learning_unit_year.find_gte_year_acronym(academic_yr, acronym).first()
    old_learning_unit_year = mdl.learning_unit_year.find_lt_year_acronym(academic_yr, acronym).last()
    if old_learning_unit_year:
        last_using = str(old_learning_unit_year.academic_year)
        existed_acronym = True

    if learning_unit_year:
        first_using = str(learning_unit_year.academic_year)
        existing_acronym = True

    if type == PARTIM:
        valid = bool(re.match(LEARNING_UNIT_ACRONYM_REGEX_ALL, acronym))
    elif type == FULL:
        valid = bool(re.match(LEARNING_UNIT_ACRONYM_REGEX_FULL, acronym))
    else:
        valid = False
    return JsonResponse({'valid': valid, 'existing_acronym': existing_acronym, 'existed_acronym': existed_acronym,
                         'first_using': first_using, 'last_using': last_using}, safe=False)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_units_activity(request):
    return _learning_units_search(request, SIMPLE_SEARCH)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_units_service_course(request):
    return _learning_units_search(request, SERVICE_COURSES_SEARCH)


def _learning_units_search(request, search_type):
    service_course_search = search_type == SERVICE_COURSES_SEARCH

    form = LearningUnitYearForm(request.GET or None, service_course_search=service_course_search)

    found_learning_units = []
    try:
        if form.is_valid():
            found_learning_units = form.get_activity_learning_units()

            check_if_display_message(request, found_learning_units)
    except TooManyResultsException:
        messages.add_message(request, messages.ERROR, _('too_many_results'))

    if request.GET.get('xls_status') == "xls":
        return create_xls(request.user, found_learning_units)

    context = {
        'form': form,
        'academic_years': get_last_academic_years(),
        'container_types': learning_container_year_types.LEARNING_CONTAINER_YEAR_TYPES,
        'types': learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES,
        'learning_units': found_learning_units,
        'current_academic_year': mdl.academic_year.current_academic_year(),
        'experimental_phase': True,
        'search_type': search_type
    }
    return layout.render(request, "learning_units.html", context)


def check_if_display_message(request, results):
    if not results:
        messages.add_message(request, messages.WARNING, _('no_result'))
    return True


def _learning_unit_volumes_management_edit(request, learning_unit_year_id):
    volumes_encoded = extract_volumes_from_data(request.POST.dict())

    try:
        return learning_unit_year_volumes.update_volumes(learning_unit_year_id, volumes_encoded)
    except (IntegrityError, ValueError) as e:
        return e.args[0]


@login_required
def learning_unit_summary(request, learning_unit_year_id):
    if not is_summary_submission_opened():
        return redirect(reverse_lazy('outside_summary_submission_period'))

    learning_unit_year = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)
    if not can_access_summary(request.user, learning_unit_year):
        raise PermissionDenied("User is not summary responsible")

    user_language = mdl.person.get_user_interface_language(request.user)
    return layout.render(request, "my_osis/educational_information.html", {
        'learning_unit_year': learning_unit_year,
        'cms_labels_translated': get_cms_label_data(CMS_LABEL_SUMMARY, user_language),
        'form_french': initialize_learning_unit_pedagogy_form(learning_unit_year, settings.LANGUAGE_CODE_FR),
        'form_english': initialize_learning_unit_pedagogy_form(learning_unit_year, settings.LANGUAGE_CODE_EN)
    })


@login_required
@require_http_methods(["GET", "POST"])
def summary_edit(request, learning_unit_year_id):
    if not is_summary_submission_opened():
        return redirect(reverse_lazy("outside_summary_submission_period"))

    learning_unit_year = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)
    if not can_access_summary(request.user, learning_unit_year):
        raise PermissionDenied("User is not summary responsible")

    if request.method == 'POST':
        form = LearningUnitPedagogyEditForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect("learning_unit_summary", learning_unit_year_id=learning_unit_year_id)
    label_name = request.GET.get('label')
    lang = request.GET.get('language')
    text_lb = text_label.find_root_by_name(label_name)
    form = LearningUnitPedagogyEditForm(**{'learning_unit_year': learning_unit_year, 'language': lang,
                                           'text_label': text_lb})
    form.load_initial()
    user_language = mdl.person.get_user_interface_language(request.user)
    text_label_translated = next((txt for txt in text_lb.translated_text_labels if txt.language == user_language), None)
    return layout.render(request, "my_osis/educational_information_edit.html", {
        "learning_unit_year": learning_unit_year,
        "form": form,
        "language_translated": find_language_in_settings(lang),
        "text_label_translated": text_label_translated
    })


@login_required
def outside_period(request):
    text = _('summary_responsible_denied')
    messages.add_message(request, messages.WARNING, "%s" % text)
    return render(request, "access_denied.html")


@login_required
@permission_required('base.can_create_learningunit', raise_exception=True)
@require_POST
@perms.can_create_partim
def learning_unit_year_partim_add(request, learning_unit_year_id):
    person = get_object_or_404(Person, user=request.user)
    learning_unit_year_parent = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)

    initial = compute_partim_form_initial_data(learning_unit_year_parent)
    post_data = _get_post_data_without_read_only_field(request.POST.copy())

    post_data_merged = QueryDict('', mutable=True)
    post_data_merged.update(initial)
    post_data_merged.update(post_data)
    form = CreatePartimForm(learning_unit_year_parent=learning_unit_year_parent, person=person, data=post_data_merged)
    if form.is_valid():
        _create_partim_process(request, learning_unit_year_parent, form)
        return HttpResponseRedirect(reverse("learning_unit",
                                            kwargs={'learning_unit_year_id': learning_unit_year_parent.id}))
    return layout.render(request, "learning_unit/partim_form.html", {'form': form})


@login_required
@permission_required('base.can_create_learningunit', raise_exception=True)
@require_GET
@perms.can_create_partim
def get_partim_creation_form(request, learning_unit_year_id):
    person = get_object_or_404(Person, user=request.user)
    learning_unit_year_parent = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)
    initial = compute_partim_form_initial_data(learning_unit_year_parent)
    form = CreatePartimForm(learning_unit_year_parent=learning_unit_year_parent, person=person, initial=initial)
    return layout.render(request, "learning_unit/partim_form.html", {'form': form})


def _get_post_data_without_read_only_field(post_data):
    post_data_without_read_only = post_data.copy()
    for read_only_field in PARTIM_FORM_READ_ONLY_FIELD:
        post_data_without_read_only.pop(read_only_field, None)
    return post_data_without_read_only


def _create_partim_process(request, learning_unit_year_parent, form):
    data = form.cleaned_data
    year = data['academic_year'].year
    parent_end_year = learning_unit_year_parent.learning_unit.end_year
    learning_container = learning_unit_year_parent.learning_container_year.learning_container
    learning_unit_created = create_learning_unit(data, learning_container, year, parent_end_year)
    while (year <= compute_max_academic_year_adjournment()) and (not parent_end_year or year <= parent_end_year):
        academic_year = mdl.academic_year.find_academic_year_by_year(year)
        luy_created = create_learning_unit_partim_structure({
            'requirement_entity_version': data.get('requirement_entity'),
            'additional_requirement_entity_version_1': data.get('additional_requirement_entity_1'),
            'additional_requirement_entity_version_2': data.get('additional_requirement_entity_2'),
            'allocation_entity_version': data.get('allocation_entity'),
            'data': data,
            'learning_container': learning_container,
            'new_learning_unit': learning_unit_created,
            'status': data['status'],
            'academic_year': academic_year
        })
        _show_success_learning_unit_year_creation_message(request, luy_created)
        year += 1


def _show_success_learning_unit_year_creation_message(request, learning_unit_year_created):
    link = reverse("learning_unit", kwargs={'learning_unit_year_id': learning_unit_year_created.id})
    success_msg = _('learning_unit_successfuly_created') % {'link': link,
                                                            'acronym': learning_unit_year_created.acronym,
                                                            'academic_year': learning_unit_year_created.academic_year}
    messages.add_message(request, messages.SUCCESS, success_msg, extra_tags='safe')


def compute_partim_form_initial_data(learning_unit_year_parent):
    initial = compute_form_initial_data(learning_unit_year_parent)
    initial['subtype'] = learning_unit_year_subtypes.PARTIM
    return initial


def compute_form_initial_data(learning_unit_year):
    other_fields_dict = {
        "first_letter": learning_unit_year.acronym[0],
        "acronym": learning_unit_year.acronym[1:]
    }
    fields = {
        "learning_unit_year":
            ("academic_year", "status", "credits", "session", "quadrimester", "subtype", "internship_subtype"),
        "learning_container_year":
            ("common_title", "common_title_english", "container_type", "campus", "language"),
        "learning_unit":
            ("faculty_remark", "other_remark", "periodicity")
    }
    return compute_learning_unit_form_initial_data(other_fields_dict, learning_unit_year, fields)


def compute_learning_unit_form_initial_data(base_dict, learning_unit_year, fields):
    initial_data = base_dict.copy()
    initial_data.update(model_to_dict(learning_unit_year, fields=fields["learning_unit_year"]))
    initial_data.update(model_to_dict(learning_unit_year.learning_container_year,
                                      fields=fields["learning_container_year"]))
    initial_data.update(model_to_dict(learning_unit_year.learning_unit,
                                      fields=fields["learning_unit"]))
    initial_data.update(get_attributions_of_learning_unit_year(learning_unit_year))
    return {key: value for key, value in initial_data.items() if value is not None}


def get_attributions_of_learning_unit_year(learning_unit_year):
    attributions = entity_container_year.find_last_entity_version_grouped_by_linktypes(
        learning_unit_year.learning_container_year
    )
    return {k.lower(): v.id for k, v in attributions.items()}


def get_learning_unit_identification_context(learning_unit_year_id, person):
    context = _get_common_context_learning_unit_year(learning_unit_year_id, person)
    learning_unit_year = context['learning_unit_year']
    context['learning_container_year_partims'] = learning_unit_year.get_partims_related()
    context['organization'] = get_organization_from_learning_unit_year(learning_unit_year)
    context['campus'] = get_campus_from_learning_unit_year(learning_unit_year)
    context['experimental_phase'] = True
    context['show_subtype'] = show_subtype(learning_unit_year)
    context.update(get_all_attributions(learning_unit_year))
    context['components'] = get_components_identification(learning_unit_year)
    context['can_propose'] = business_perms.is_eligible_for_modification_proposal(learning_unit_year, person)
    context['can_edit_date'] = business_perms.is_eligible_for_modification_end_date(learning_unit_year, person)
    context['can_edit'] = business_perms.is_eligible_for_modification(learning_unit_year, person)
    context['proposal'] = proposal_learning_unit.find_by_learning_unit_year(learning_unit_year)
    context['can_cancel_proposal'] = business_perms. \
        is_eligible_for_cancel_of_proposal(context['proposal'], person) if context['proposal'] else False
    context['proposal_folder_entity_version'] = mdl_base.entity_version.get_by_entity_and_date(
        context['proposal'].folder.entity, None) if context['proposal'] else None
    context['can_delete'] = learning_unit_deletion.can_delete_learning_unit_year(person, learning_unit_year)
    return context
