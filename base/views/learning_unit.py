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
import datetime
from collections import OrderedDict
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods
from base import models as mdl
from base.business import learning_unit_year_volumes
from base.business import learning_unit_year_with_context
from attribution import models as mdl_attr
from base.decorators import cache_filter
from base.business.learning_unit_year_with_context import volume_learning_component_year
from base.models import entity_container_year
from base.models.entity_component_year import EntityComponentYear
from base.models.entity_container_year import EntityContainerYear
from base.models.enums import entity_container_year_link_type
from base.models.enums import learning_container_year_types
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY, ALLOCATION_ENTITY, \
    ADDITIONAL_REQUIREMENT_ENTITY_1, ADDITIONAL_REQUIREMENT_ENTITY_2
from base.models.enums.learning_component_year_type import PRACTICAL_EXERCISES, LECTURING
from base.models.enums.learning_container_year_types import COURSE
from base.models.enums.learning_unit_year_subtypes import FULL
from base.models.learning_component_year import LearningComponentYear
from base.models.learning_container import LearningContainer
from base.models.learning_container_year import LearningContainerYear
from base.models.learning_unit import LearningUnit
from base.models.learning_unit_component import LearningUnitComponent
from base.models.learning_unit_year import LearningUnitYear
from cms import models as mdl_cms
from cms.enums import entity_name
from base.forms.learning_units import LearningUnitYearForm, CreateLearningUnitYearForm, MAX_RECORDS
from base.forms.learning_unit_specifications import LearningUnitSpecificationsForm, LearningUnitSpecificationsEditForm
from base.forms.learning_unit_pedagogy import LearningUnitPedagogyForm, LearningUnitPedagogyEditForm
from base.forms.learning_unit_component import LearningUnitComponentEditForm
from base.forms.learning_class import LearningClassEditForm
from base.models.enums import learning_unit_year_subtypes
from cms.models import text_label
from reference.models.language import find_by_id
from . import layout
from django.http import JsonResponse


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@cache_filter()
def learning_units(request):
    return learning_units_search(request, 1)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_identification(request, learning_unit_year_id):
    context = _get_common_context_learning_unit_year(learning_unit_year_id)
    learning_unit_year = context['learning_unit_year']
    context['learning_container_year_partims'] = _get_partims_related(learning_unit_year)
    context['organization'] = _get_organization_from_learning_unit_year(learning_unit_year)
    context['campus'] = _get_campus_from_learning_unit_year(learning_unit_year)
    context['experimental_phase'] = True
    context['show_subtype'] = _show_subtype(learning_unit_year)
    context.update(_get_all_attributions(learning_unit_year))
    context['components'] = get_components_identification(learning_unit_year)

    return layout.render(request, "learning_unit/identification.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_formations(request, learning_unit_year_id):
    context = _get_common_context_learning_unit_year(learning_unit_year_id)
    return layout.render(request, "learning_unit/formations.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_components(request, learning_unit_year_id):
    context = _get_common_context_learning_unit_year(learning_unit_year_id)
    context['components'] = get_same_container_year_components(context['learning_unit_year'], True)
    context['tab_active'] = 'components'
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/components.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def volumes_validation(request, learning_unit_year_id):
    volumes_encoded = _extract_volumes_from_data(request)
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

    context = _get_common_context_learning_unit_year(learning_unit_year_id)
    context['learning_units'] = learning_unit_year_with_context.get_with_context(
        learning_container_year_id=context['learning_unit_year'].learning_container_year_id
    )
    context['tab_active'] = 'components'
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/volumes_management.html", context)


def _learning_unit_volumes_management_edit(request, learning_unit_year_id):
    errors = None
    volumes_encoded = _extract_volumes_from_data(request)

    try:
        errors = learning_unit_year_volumes.update_volumes(learning_unit_year_id, volumes_encoded)
    except Exception as e:
        error_msg = e.messages[0] if isinstance(e, ValidationError) else e.args[0]
        messages.add_message(request, messages.ERROR, _(error_msg))

    if errors:
        for error_msg in errors:
            messages.add_message(request, messages.ERROR, error_msg)


def _extract_volumes_from_data(request):
    volumes = {}
    post_data = request.POST.dict()

    for param, value in post_data.items():
        param_splitted = param.rsplit("_", 2)
        key = param_splitted[0]
        if _is_a_valid_volume_key(key) and len(param_splitted) == 3:   # KEY_[LEARNINGUNITYEARID]_[LEARNINGCOMPONENTID]
            learning_unit_year_id = int(param_splitted[1])
            component_id = int(param_splitted[2])
            volumes.setdefault(learning_unit_year_id, {}).setdefault(component_id, {}).update({key: value})
    return volumes


def _is_a_valid_volume_key(post_key):
    return post_key in learning_unit_year_volumes.VALID_VOLUMES_KEYS


def _perserve_volume_encoded(request, context):
    pass


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_pedagogy(request, learning_unit_year_id):
    context = _get_common_context_learning_unit_year(learning_unit_year_id)
    learning_unit_year = context['learning_unit_year']

    CMS_LABEL = ['resume', 'bibliography', 'teaching_methods', 'evaluation_methods',
                 'other_informations', 'online_resources']
    user_language = mdl.person.get_user_interface_language(request.user)
    context['cms_labels_translated'] = _get_cms_label_data(CMS_LABEL, user_language)

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
                                            kwargs={'learning_unit_year_id':learning_unit_year_id}))

    context = _get_common_context_learning_unit_year(learning_unit_year_id)
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
    context = _get_common_context_learning_unit_year(learning_unit_year_id)
    context['attributions'] = mdl_attr.attribution.find_by_learning_unit_year(learning_unit_year=learning_unit_year_id)
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/attributions.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_proposals(request, learning_unit_year_id):
    context = _get_common_context_learning_unit_year(learning_unit_year_id)
    return layout.render(request, "learning_unit/proposals.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_specifications(request, learning_unit_year_id):
    context = _get_common_context_learning_unit_year(learning_unit_year_id)
    learning_unit_year = context['learning_unit_year']

    CMS_LABEL = ['themes_discussed', 'skills_to_be_acquired', 'prerequisite']
    user_language = mdl.person.get_user_interface_language(request.user)
    context['cms_labels_translated'] = _get_cms_label_data(CMS_LABEL, user_language)

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

    context = _get_common_context_learning_unit_year(learning_unit_year_id)
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


def _check_if_display_message(request, found_learning_units):
    if not found_learning_units:
        messages.add_message(request, messages.WARNING, _('no_result'))
    else:
        if len(found_learning_units) > MAX_RECORDS:
            messages.add_message(request, messages.WARNING, _('too_many_results'))
            return False
    return True

def _get_common_context_list_learning_unit_years():
    today = datetime.date.today()
    date_ten_years_before = today.replace(year=today.year-10)
    academic_years = mdl.academic_year.find_academic_years()\
                                      .filter(start_date__gte=date_ten_years_before)

    context = {
        'academic_years': academic_years
    }
    return context


def _get_common_context_learning_unit_year(learning_unit_year_id):
    learning_unit_year = mdl.learning_unit_year.find_by_id(learning_unit_year_id)

    context = {
        'learning_unit_year': learning_unit_year,
        'current_academic_year': mdl.academic_year.current_academic_year()
    }
    return context


def get_same_container_year_components(learning_unit_year, with_classes=False):
    learning_container_year = learning_unit_year.learning_container_year
    components = []
    learning_components_year = mdl.learning_component_year.find_by_learning_container_year(learning_container_year, with_classes)

    for learning_component_year in learning_components_year:
        if learning_component_year.classes:
            for learning_class_year in learning_component_year.classes:
                learning_class_year.used_by_learning_units_year = _learning_unit_usage_by_class(learning_class_year)
                learning_class_year.is_used_by_full_learning_unit_year = _is_used_by_full_learning_unit_year(learning_class_year)

        used_by_learning_unit = mdl.learning_unit_component.search(learning_component_year, learning_unit_year)

        entity_components_yr = EntityComponentYear.objects.filter(learning_component_year=learning_component_year)

        components.append({'learning_component_year': learning_component_year,
                           'entity_component_yr': entity_components_yr.first(),
                           'volumes': volume_learning_component_year(learning_component_year, entity_components_yr),
                           'learning_unit_usage': _learning_unit_usage(learning_component_year),
                           'used_by_learning_unit': used_by_learning_unit
                           })
    return components


def _get_partims_related(learning_unit_year):
    learning_container_year = learning_unit_year.learning_container_year
    if learning_container_year:
        return mdl.learning_unit_year.search(learning_container_year_id=learning_container_year,
                                             subtype=learning_unit_year_subtypes.PARTIM)\
            .exclude(learning_container_year__isnull=True).order_by('acronym')


def _show_subtype(learning_unit_year):
    learning_container_year = learning_unit_year.learning_container_year

    if learning_container_year:
        return learning_container_year.container_type == learning_container_year_types.COURSE or \
             learning_container_year.container_type == learning_container_year_types.INTERNSHIP
    return False


def _get_campus_from_learning_unit_year(learning_unit_year):
    if learning_unit_year.learning_container_year:
        return learning_unit_year.learning_container_year.campus
    return None


def _get_organization_from_learning_unit_year(learning_unit_year):
    campus = _get_campus_from_learning_unit_year(learning_unit_year)
    if campus:
        return campus.organization
    return None


def _get_all_attributions(learning_unit_year):
    attributions = {}
    if learning_unit_year.learning_container_year:
        all_attributions = entity_container_year.find_last_entity_version_grouped_by_linktypes(learning_unit_year.learning_container_year)
        attributions['requirement_entity'] = all_attributions.get(entity_container_year_link_type.REQUIREMENT_ENTITY)
        attributions['allocation_entity'] = all_attributions.get(entity_container_year_link_type.ALLOCATION_ENTITY)
        attributions['additional_requirement_entities'] = [
            all_attributions[link_type] for link_type in all_attributions
                if link_type not in [entity_container_year_link_type.REQUIREMENT_ENTITY,
                                     entity_container_year_link_type.ALLOCATION_ENTITY]
        ]
    return attributions


def _get_cms_label_data(cms_label, user_language):
    cms_label_data = OrderedDict()
    translated_labels = mdl_cms.translated_text_label.search(text_entity=entity_name.LEARNING_UNIT_YEAR,
                                                             labels=cms_label,
                                                             language=user_language)

    for label in cms_label:
        translated_text = next((trans.label for trans in translated_labels if trans.text_label.label == label), None)
        cms_label_data[label] = translated_text

    return cms_label_data


def _learning_unit_usage(a_learning_component_year):
    learning_unit_component = mdl.learning_unit_component.find_by_learning_component_year(a_learning_component_year)
    ch = ""
    separator = ""
    for l in learning_unit_component:
        ch = "{}{}{}".format(ch, separator, l.learning_unit_year.acronym)
        separator = ", "
    return ch


def _learning_unit_usage_by_class(a_learning_class_year):
    queryset = mdl.learning_unit_component_class.find_by_learning_class_year(a_learning_class_year)\
                                            .order_by('learning_unit_component__learning_unit_year__acronym')\
                                            .values_list('learning_unit_component__learning_unit_year__acronym', flat=True)
    return ", ".join(list(queryset))


def get_components_identification(learning_unit_yr):
    a_learning_container_yr = learning_unit_yr.learning_container_year
    components = []
    if a_learning_container_yr:
        learning_component_year_list = mdl.learning_component_year.find_by_learning_container_year(a_learning_container_yr)

        for learning_component_year in learning_component_year_list:
            if mdl.learning_unit_component.search(learning_component_year, learning_unit_yr).exists():
                entity_components_yr = EntityComponentYear.objects.filter(learning_component_year=learning_component_year)

                components.append({'learning_component_year': learning_component_year,
                                   'entity_component_yr': entity_components_yr.first(),
                                   'volumes': volume_learning_component_year(learning_component_year,
                                                                             entity_components_yr),
                                   'learning_unit_usage': _learning_unit_usage(learning_component_year)})
    return components


def _is_used_by_full_learning_unit_year(a_learning_class_year):
    learning_unit_component_class = mdl.learning_unit_component_class.find_by_learning_class_year(a_learning_class_year)
    for index, l in enumerate(learning_unit_component_class):
        if l.learning_unit_component.learning_unit_year.subdivision is None:
            return True

    return False


@login_required
@permission_required('base.change_learningcomponentyear', raise_exception=True)
@require_http_methods(["GET", "POST"])
def learning_unit_component_edit(request, learning_unit_year_id):
    context = _get_common_context_learning_unit_year(learning_unit_year_id)
    learning_component_id = request.GET.get('learning_component_year_id')
    context['learning_component_year'] = mdl.learning_component_year.find_by_id(learning_component_id)

    if request.method == 'POST':
        form = LearningUnitComponentEditForm(request.POST,
                                             learning_unit_year=context['learning_unit_year'],
                                             instance=context['learning_component_year'])
        if form.is_valid():
            form.save()
        return HttpResponseRedirect(reverse("learning_unit_components",
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
    context = _get_common_context_learning_unit_year(learning_unit_year_id)
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


def learning_unit_create(request, academic_year):
    form = CreateLearningUnitYearForm(initial={'academic_year': academic_year,
                                               'subtype': FULL,
                                               'learning_container_year_type': "---------",
                                               'language': 3})
    return layout.render(request, "learning_unit/learning_unit_form.html", {'form': form})


def learning_unit_year_add(request):
    if request.POST:
        form = CreateLearningUnitYearForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            starting_academic_year = mdl.academic_year.starting_academic_year()
            academic_year = data['academic_year']
            year = academic_year.year
            status = check_status(data)
            additional_entity_version_1 = None
            additional_entity_version_2 = None
            allocation_entity_version = None
            requirement_entity_version = mdl.entity_version.find_by_id(data['requirement_entity'])
            if data['allocation_entity']:
                allocation_entity_version = mdl.entity_version.find_by_id(data['allocation_entity'])
            if data['additional_entity_1']:
                additional_entity_version_1 = mdl.entity_version.find_by_id(data['additional_entity_1'])
            if data['additional_entity_2']:
                additional_entity_version_2 = mdl.entity_version.find_by_id(data['additional_entity_2'])
            new_learning_container = create_learning_container(year)
            new_learning_unit = create_learning_unit(data, new_learning_container, year)
            while year < starting_academic_year.year+6:
                academic_year = mdl.academic_year.find_academic_year_by_year(year)
                create_learning_unit_structure(additional_entity_version_1, additional_entity_version_2,
                                               allocation_entity_version, data, form, new_learning_container,
                                               new_learning_unit, requirement_entity_version, status, academic_year)
                year = year+1
            return redirect('learning_units')
        else:
            return layout.render(request, "learning_unit/learning_unit_form.html", {'form': form})
    else:
        return redirect('learning_unit_create')


def create_learning_unit_structure(additional_entity_version_1, additional_entity_version_2, allocation_entity_version,
                                   data, form, new_learning_container, new_learning_unit, requirement_entity_version,
                                   status, academic_year):
    new_learning_container_year = create_learning_container_year(academic_year, data,
                                                                 new_learning_container)
    new_requirement_entity = create_entity_container_year(requirement_entity_version,
                                                          new_learning_container_year,
                                                          REQUIREMENT_ENTITY)
    if allocation_entity_version:
        create_entity_container_year(allocation_entity_version, new_learning_container_year, ALLOCATION_ENTITY)
    if additional_entity_version_1:
        create_entity_container_year(additional_entity_version_1, new_learning_container_year,
                                     ADDITIONAL_REQUIREMENT_ENTITY_1)
    if additional_entity_version_2:
        create_entity_container_year(additional_entity_version_2, new_learning_container_year,
                                     ADDITIONAL_REQUIREMENT_ENTITY_2)
    if data['learning_container_year_type'] == COURSE:
        create_course(academic_year, form, new_learning_container_year, new_learning_unit,
                      new_requirement_entity, status)
    else:
        create_another_type(academic_year, form, new_learning_container_year, new_learning_unit,
                            new_requirement_entity, status)


def create_another_type(an_academic_year, form, new_learning_container_year, new_learning_unit, new_requirement_entity,
                        status):
    new_learning_component_year = create_learning_component_year(new_learning_container_year,
                                                                 "NT1", None)
    create_entity_component_year(new_requirement_entity, new_learning_component_year)
    new_learning_unit_year = create_learning_unit_year(an_academic_year, form,
                                                       new_learning_container_year,
                                                       new_learning_unit,
                                                       status)
    create_learning_unit_component(new_learning_unit_year, new_learning_component_year, None)


def create_course(an_academic_year, form, new_learning_container_year, new_learning_unit,
                  new_requirement_entity, status):
    new_lecturing = create_learning_component_year(new_learning_container_year, "CM1", LECTURING)
    new_practical_exercise = create_learning_component_year(new_learning_container_year, "TP1",
                                                            PRACTICAL_EXERCISES)
    create_entity_component_year(new_requirement_entity, new_lecturing)
    create_entity_component_year(new_requirement_entity, new_practical_exercise)
    new_learning_unit_year = create_learning_unit_year(an_academic_year, form,
                                                       new_learning_container_year,
                                                       new_learning_unit,
                                                       status)
    create_learning_unit_component(new_learning_unit_year, new_lecturing, LECTURING)
    create_learning_unit_component(new_learning_unit_year, new_practical_exercise, PRACTICAL_EXERCISES)


def check_status(data):
    if data['status'] == 'on':
        status = True
    else:
        status = False
    return status


def create_learning_component_year(learning_container_year, acronym, type):
    new_lecturing = LearningComponentYear(learning_container_year=learning_container_year,
                                          acronym=acronym,
                                          type=type)
    new_lecturing.save()
    return new_lecturing


def create_learning_unit_component(learning_unit_year, learning_component_year, type):
    new_learning_unit_component = LearningUnitComponent(learning_unit_year=learning_unit_year,
                                                        learning_component_year=learning_component_year,
                                                        type=type)
    new_learning_unit_component.save()
    return new_learning_unit_component


def create_entity_component_year(entity_container_year, learning_component_year):
    new_entity_component_year = EntityComponentYear(entity_container_year=entity_container_year,
                                                    learning_component_year=learning_component_year)
    new_entity_component_year.save()
    return new_entity_component_year


def create_learning_container(year):
    new_learning_container = LearningContainer(start_year=year)
    new_learning_container.save()
    return new_learning_container


def create_learning_container_year(academic_year, data, learning_container):
    a_language = find_by_id(data['language'])
    new_learning_container_year = LearningContainerYear(academic_year=academic_year,
                                                        learning_container=learning_container,
                                                        title=data['title'],
                                                        acronym=data['acronym'].upper(),
                                                        container_type=data['learning_container_year_type'],
                                                        language=a_language)
    new_learning_container_year.save()
    return new_learning_container_year


def create_entity_container_year(entity_version, learning_container_year, type):
    new_entity_container_year = EntityContainerYear(entity=entity_version.entity,
                                                    learning_container_year=learning_container_year,
                                                    type=type)
    new_entity_container_year.save()
    return new_entity_container_year


def create_learning_unit(data, learning_container, year):
    new_learning_unit = LearningUnit(acronym=data['acronym'].upper(), title=data['title'], start_year=year,
                                     periodicity=data['periodicity'], learning_container=learning_container,
                                     faculty_remark=data['faculty_remark'], other_remark=data['other_remark'])
    new_learning_unit.save()
    return new_learning_unit


def create_learning_unit_year(academic_year, form, learning_container_year, learning_unit, status):
    if form.data.get('internship_subtype'):
        internship_subtype = form.data['internship_subtype']
    else:
        internship_subtype = None
    new_learning_unit_year = LearningUnitYear(academic_year=academic_year, learning_unit=learning_unit,
                                              learning_container_year=learning_container_year,
                                              acronym=form.data['acronym'].upper(),
                                              title=form.data['title'],
                                              title_english=form.data['title_english'],
                                              subtype=form.data['subtype'],
                                              credits=form.data['credits'],
                                              internship_subtype=internship_subtype,
                                              status=status,
                                              session=form.data['session'])
    new_learning_unit_year.save()
    return new_learning_unit_year


def check_acronym(request):
    acronym = request.GET['acronym']
    year_id = request.GET['year_id']
    academic_yr = mdl.academic_year.find_academic_year_by_id(year_id)
    valid = True
    existed_acronym = False
    existing_acronym = False
    learning_unit_years = mdl.learning_unit_year.find_gte_year_acronym(academic_yr, acronym)
    old_learning_unit_year = mdl.learning_unit_year.find_lt_year_acronym(academic_yr, acronym).last()
    if old_learning_unit_year:
        last_using = str(old_learning_unit_year.academic_year)
    else:
        last_using = ""
    if old_learning_unit_year:
        existed_acronym = True
        valid = True
    if learning_unit_years:
        existing_acronym = True
        valid = False

    return JsonResponse({'valid': valid,
                         'existing_acronym': existing_acronym,
                         'existed_acronym': existed_acronym,
                         'last_using': last_using}, safe=False)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@cache_filter()
def learning_units_activity(request):
    return learning_units_search(request, 1)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
@cache_filter()
def learning_units_service_course(request):
    return learning_units_search(request, 2)

def learning_units_search(request, search_type):
    if request.GET.get('academic_year_id'):
        form = LearningUnitYearForm(request.GET)
    else:
        form = LearningUnitYearForm()
    found_learning_units = None
    if form.is_valid():
        if search_type == 1:
            found_learning_units = form.get_activity_learning_units()
        else:
            if search_type == 2:
                found_learning_units = form.get_service_course_learning_units()
        _check_if_display_message(request, found_learning_units)

    context = _get_common_context_list_learning_unit_years()
    context.update({
        'form': form,
        'academic_years': mdl.academic_year.find_academic_years(),
        'container_types': learning_container_year_types.LEARNING_CONTAINER_YEAR_TYPES,
        'types': learning_unit_year_subtypes.LEARNING_UNIT_YEAR_SUBTYPES,
        'learning_units': found_learning_units,
        'current_academic_year': mdl.academic_year.current_academic_year(),
        'experimental_phase': True,
        'search_type': search_type
    })
    return layout.render(request, "learning_units.html", context)