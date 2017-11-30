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
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect, get_object_or_404
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from base import models as mdl
from base.business import learning_unit_year_volumes
from base.business import learning_unit_year_with_context
from attribution import models as mdl_attr
from base.business.learning_unit import create_learning_unit, create_learning_unit_structure, \
    get_common_context_learning_unit_year, get_cms_label_data, \
    extract_volumes_from_data, get_same_container_year_components, get_components_identification, show_subtype, \
    get_organization_from_learning_unit_year, get_campus_from_learning_unit_year, \
    get_all_attributions, get_last_academic_years
from base.forms.common import TooManyResultsException
from base.models import proposal_learning_unit, entity_version
from base.models.enums import learning_container_year_types
from base.models.enums.learning_unit_year_subtypes import FULL
from base.models.learning_container import LearningContainer
from base.forms.learning_units import LearningUnitYearForm, CreateLearningUnitYearForm, EMPTY_FIELD
from base.forms.learning_unit_specifications import LearningUnitSpecificationsForm, LearningUnitSpecificationsEditForm
from base.forms.learning_unit_pedagogy import LearningUnitPedagogyForm, LearningUnitPedagogyEditForm
from base.forms.learning_unit_component import LearningUnitComponentEditForm
from base.forms.learning_class import LearningClassEditForm
from base.models.enums import learning_unit_year_subtypes
from base.models.person import Person
from cms.models import text_label
from reference.models import language
from . import layout

CMS_LABEL_SPECIFICATIONS = ['themes_discussed', 'skills_to_be_acquired', 'prerequisite']
CMS_LABEL_PEDAGOGY = ['resume', 'bibliography', 'teaching_methods', 'evaluation_methods',
                      'other_informations', 'online_resources']

LEARNING_UNIT_CREATION_SPAN_YEARS = 6

SIMPLE_SEARCH = 1
SERVICE_COURSES_SEARCH = 2


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
    context = get_common_context_learning_unit_year(learning_unit_year_id)
    learning_unit_year = context['learning_unit_year']
    context['learning_container_year_partims'] = learning_unit_year.get_partims_related()
    context['organization'] = get_organization_from_learning_unit_year(learning_unit_year)
    context['campus'] = get_campus_from_learning_unit_year(learning_unit_year)
    context['experimental_phase'] = True
    context['show_subtype'] = show_subtype(learning_unit_year)
    context.update(get_all_attributions(learning_unit_year))
    context['components'] = get_components_identification(learning_unit_year)
    context['proposal'] = proposal_learning_unit.find_by_learning_unit_year(learning_unit_year)
    context['proposal_folder_entity_version'] = \
        entity_version.get_by_entity_and_date(context['proposal'].folder.entity, None) if context['proposal'] else None

    return layout.render(request, "learning_unit/identification.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_formations(request, learning_unit_year_id):
    context = get_common_context_learning_unit_year(learning_unit_year_id)
    return layout.render(request, "learning_unit/formations.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_components(request, learning_unit_year_id):
    context = get_common_context_learning_unit_year(learning_unit_year_id)
    context['components'] = get_same_container_year_components(context['learning_unit_year'], True)
    context['tab_active'] = 'components'
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
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_volumes_management(request, learning_unit_year_id):
    if request.method == 'POST':
        _learning_unit_volumes_management_edit(request, learning_unit_year_id)

    context = get_common_context_learning_unit_year(learning_unit_year_id)
    context['learning_units'] = learning_unit_year_with_context.get_with_context(
        learning_container_year_id=context['learning_unit_year'].learning_container_year_id
    )
    context['tab_active'] = 'components'
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/volumes_management.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_pedagogy(request, learning_unit_year_id):
    context = get_common_context_learning_unit_year(learning_unit_year_id)
    learning_unit_year = context['learning_unit_year']

    user_language = mdl.person.get_user_interface_language(request.user)
    context['cms_labels_translated'] = get_cms_label_data(CMS_LABEL_PEDAGOGY, user_language)

    fr_language = next((lang for lang in settings.LANGUAGES if lang[0] == 'fr-be'), None)
    en_language = next((lang for lang in settings.LANGUAGES if lang[0] == 'en'), None)
    context.update({
        'form_french': LearningUnitPedagogyForm(learning_unit_year=learning_unit_year,
                                                language=fr_language),
        'form_english': LearningUnitPedagogyForm(learning_unit_year=learning_unit_year,
                                                 language=en_language)
    })
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

    context = get_common_context_learning_unit_year(learning_unit_year_id)
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
    context['language_translated'] = next((lang for lang in settings.LANGUAGES if lang[0] == language), None)
    return layout.render(request, "learning_unit/pedagogy_edit.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_attributions(request, learning_unit_year_id):
    context = get_common_context_learning_unit_year(learning_unit_year_id)
    context['attributions'] = mdl_attr.attribution.find_by_learning_unit_year(learning_unit_year=learning_unit_year_id)
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/attributions.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_specifications(request, learning_unit_year_id):
    context = get_common_context_learning_unit_year(learning_unit_year_id)
    learning_unit_year = context['learning_unit_year']

    user_language = mdl.person.get_user_interface_language(request.user)
    context['cms_labels_translated'] = get_cms_label_data(CMS_LABEL_SPECIFICATIONS, user_language)

    fr_language = next((lang for lang in settings.LANGUAGES if lang[0] == 'fr-be'), None)
    en_language = next((lang for lang in settings.LANGUAGES if lang[0] == 'en'), None)

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

    context = get_common_context_learning_unit_year(learning_unit_year_id)
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
    context['language_translated'] = next((lang for lang in settings.LANGUAGES if lang[0] == language), None)
    return layout.render(request, "learning_unit/specifications_edit.html", context)


@login_required
@permission_required('base.change_learningcomponentyear', raise_exception=True)
@require_http_methods(["GET", "POST"])
def learning_unit_component_edit(request, learning_unit_year_id):
    context = get_common_context_learning_unit_year(learning_unit_year_id)
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
    context = get_common_context_learning_unit_year(learning_unit_year_id)
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
                                                       'subtype': FULL,
                                                       "container_type": EMPTY_FIELD,
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
        starting_academic_year = mdl.academic_year.starting_academic_year()
        academic_year = data['academic_year']
        year = academic_year.year
        status = data['status'] == 'on'
        additional_entity_version_1 = data.get('additional_entity_1')
        additional_entity_version_2 = data.get('additional_entity_2')
        allocation_entity_version = data.get('allocation_entity')
        requirement_entity_version = data.get('requirement_entity')

        new_learning_container = LearningContainer.objects.create(start_year=year)
        new_learning_unit = create_learning_unit(data, new_learning_container, year)
        while year < starting_academic_year.year + LEARNING_UNIT_CREATION_SPAN_YEARS:
            academic_year = mdl.academic_year.find_academic_year_by_year(year)

            create_learning_unit_structure(additional_entity_version_1, additional_entity_version_2,
                                           allocation_entity_version, data, new_learning_container,
                                           new_learning_unit, requirement_entity_version, status, academic_year)
            year += 1
        return redirect('learning_units')
    else:
        return layout.render(request, "learning_unit/learning_unit_form.html", {'form': form})


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def check_acronym(request):
    acronym = request.GET['acronym']
    year_id = request.GET['year_id']
    academic_yr = mdl.academic_year.find_academic_year_by_id(year_id)
    valid = True
    existed_acronym = False
    existing_acronym = False
    last_using = ""

    learning_unit_years = mdl.learning_unit_year.find_gte_year_acronym(academic_yr, acronym)
    old_learning_unit_year = mdl.learning_unit_year.find_lt_year_acronym(academic_yr, acronym).last()

    if old_learning_unit_year:
        last_using = str(old_learning_unit_year.academic_year)
        existed_acronym = True

    if learning_unit_years:
        existing_acronym = True
        valid = False

    return JsonResponse({'valid': valid,
                         'existing_acronym': existing_acronym,
                         'existed_acronym': existed_acronym,
                         'last_using': last_using}, safe=False)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def check_code(request):
    campus_id = request.GET['campus']
    campus = mdl.campus.find_by_id(campus_id)
    return JsonResponse({'code': campus.code}, safe=False)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_units_activity(request):
    return _learning_units_search(request, SIMPLE_SEARCH)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_units_service_course(request):
    return _learning_units_search(request, SERVICE_COURSES_SEARCH)


def _learning_units_search(request, search_type):
    if request.GET.get('academic_year_id'):
        form = LearningUnitYearForm(request.GET)
    else:
        form = LearningUnitYearForm()

    found_learning_units = None
    try:
        if form.is_valid():

            if search_type == SIMPLE_SEARCH:
                found_learning_units = form.get_activity_learning_units()
            elif search_type == SERVICE_COURSES_SEARCH:
                found_learning_units = form.get_service_course_learning_units()

            _check_if_display_message(request, found_learning_units)
    except TooManyResultsException:
        messages.add_message(request, messages.ERROR, _('too_many_results'))

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


def _check_if_display_message(request, found_learning_units):
    if not found_learning_units:
        messages.add_message(request, messages.WARNING, _('no_result'))
    return True


def _learning_unit_volumes_management_edit(request, learning_unit_year_id):
    errors = None
    volumes_encoded = extract_volumes_from_data(request.POST.dict())

    try:
        errors = learning_unit_year_volumes.update_volumes(learning_unit_year_id, volumes_encoded)
    except Exception as e:
        error_msg = e.messages[0] if isinstance(e, ValidationError) else e.args[0]
        messages.add_message(request, messages.ERROR, _(error_msg))

    if errors:
        for error_msg in errors:
            messages.add_message(request, messages.ERROR, error_msg)
