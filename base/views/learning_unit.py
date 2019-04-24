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
from copy import deepcopy

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.core.urlresolvers import reverse
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods

from attribution.business import attribution_charge_new
from attribution.models.attribution_charge_new import AttributionChargeNew
from attribution.models.enums.function import Functions
from base import models as mdl
from base.business.learning_unit import get_cms_label_data, \
    get_same_container_year_components, CMS_LABEL_SPECIFICATIONS, get_achievements_group_by_language, \
    get_components_identification
from base.business.learning_unit_proposal import _get_value_from_enum
from base.business.learning_units import perms as business_perms
from base.business.learning_units.comparison import get_entity_by_type, \
    FIELDS_FOR_LEARNING_UNIT_YR_COMPARISON, FIELDS_FOR_LEARNING_CONTAINER_YR_COMPARISON
from base.business.learning_units.perms import can_update_learning_achievement
from base.forms.learning_unit_specifications import LearningUnitSpecificationsForm, LearningUnitSpecificationsEditForm
from base.models import education_group_year, campus, proposal_learning_unit, entity
from base.models import learning_component_year as mdl_learning_component_year
from base.models.enums import learning_unit_year_subtypes
from base.models.enums.attribution_procedure import ATTRIBUTION_PROCEDURES
from base.models.enums.entity_container_year_link_type import ENTITY_TYPE_LIST, EntityContainerYearLinkTypes
from base.models.enums.learning_component_year_type import LEARNING_COMPONENT_YEAR_TYPES
from base.models.enums.learning_unit_year_periodicity import PERIODICITY_TYPES
from base.models.enums.vacant_declaration_type import DECLARATION_TYPE
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.views.common import display_warning_messages
from base.views.learning_units.common import get_common_context_learning_unit_year, get_text_label_translated
from cms.models import text_label
from reference.models import language
from reference.models.language import find_language_in_settings

ORGANIZATION_KEYS = ['ALLOCATION_ENTITY', 'REQUIREMENT_ENTITY',
                     'ADDITIONAL_REQUIREMENT_ENTITY_1', 'ADDITIONAL_REQUIREMENT_ENTITY_2',
                     'campus', 'organization']


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_formations(request, learning_unit_year_id):
    context = get_common_context_learning_unit_year(learning_unit_year_id, get_object_or_404(Person, user=request.user))
    learn_unit_year = context["learning_unit_year"]
    group_elements_years = learn_unit_year.child_leaf.select_related(
        "parent", "child_leaf", "parent__education_group_type"
    ).order_by('parent__partial_acronym')
    education_groups_years = [group_element_year.parent for group_element_year in group_elements_years]
    formations_by_educ_group_year = mdl.group_element_year.find_learning_unit_formations(education_groups_years,
                                                                                         parents_as_instances=True)
    context['formations_by_educ_group_year'] = formations_by_educ_group_year
    context['group_elements_years'] = group_elements_years

    context['root_formations'] = education_group_year.find_with_enrollments_count(learn_unit_year)
    context['experimental_phase'] = True

    return render(request, "learning_unit/formations.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_components(request, learning_unit_year_id):
    person = get_object_or_404(Person, user=request.user)
    context = get_common_context_learning_unit_year(learning_unit_year_id, person)
    learning_unit_year = context['learning_unit_year']
    context['warnings'] = learning_unit_year.warnings
    data_components = get_same_container_year_components(context['learning_unit_year'])
    context['components'] = data_components.get('components')
    context['REQUIREMENT_ENTITY'] = data_components.get('REQUIREMENT_ENTITY')
    context['ADDITIONAL_REQUIREMENT_ENTITY_1'] = data_components.get('ADDITIONAL_REQUIREMENT_ENTITY_1')
    context['ADDITIONAL_REQUIREMENT_ENTITY_2'] = data_components.get('ADDITIONAL_REQUIREMENT_ENTITY_2')
    context['tab_active'] = 'components'
    context['can_manage_volume'] = business_perms.is_eligible_for_modification(context["learning_unit_year"], person)
    context['experimental_phase'] = True
    return render(request, "learning_unit/components.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_attributions(request, learning_unit_year_id):
    context = get_common_context_learning_unit_year(learning_unit_year_id, request.user.person)

    context['attributions'] = attribution_charge_new.find_attributions_with_charges(learning_unit_year_id)
    context["can_manage_charge_repartition"] = business_perms.is_eligible_to_manage_charge_repartition(
        context["learning_unit_year"], request.user.person
    )
    context["can_manage_attribution"] = business_perms.is_eligible_to_manage_attributions(
        context["learning_unit_year"], request.user.person
    )
    context['experimental_phase'] = True

    warning_msgs = get_charge_repartition_warning_messages(context["learning_unit_year"].learning_container_year)
    display_warning_messages(request, warning_msgs)
    return render(request, "learning_unit/attributions.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_specifications(request, learning_unit_year_id):
    person = get_object_or_404(Person, user=request.user)
    context = get_common_context_learning_unit_year(learning_unit_year_id, person)
    learning_unit_year = context['learning_unit_year']

    context.update(get_specifications_context(learning_unit_year, request))
    context.update(get_achievements_group_by_language(learning_unit_year))
    context.update(get_languages_settings())
    context['can_update_learning_achievement'] = can_update_learning_achievement(learning_unit_year, person)
    context['experimental_phase'] = True
    return render(request, "learning_unit/specifications.html", context)


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

    context = get_common_context_learning_unit_year(learning_unit_year_id,
                                                    get_object_or_404(Person, user=request.user))
    label_name = request.GET.get('label')
    text_lb = text_label.get_by_name(label_name)
    language = request.GET.get('language')
    form = LearningUnitSpecificationsEditForm(**{
        'learning_unit_year': context['learning_unit_year'],
        'language': language,
        'text_label': text_lb
    })
    form.load_initial()  # Load data from database
    context['form'] = form

    user_language = mdl.person.get_user_interface_language(request.user)
    context['text_label_translated'] = get_text_label_translated(text_lb, user_language)
    context['language_translated'] = find_language_in_settings(language)
    return render(request, "learning_unit/specifications_edit.html", context)


@login_required
def learning_unit_proposal_comparison(request, learning_unit_year_id):
    learning_unit_year = get_object_or_404(
        LearningUnitYear.objects.all().select_related('learning_unit', 'learning_container_year',
                                                      'campus', 'campus__organization'), pk=learning_unit_year_id
    )
    initial_data = proposal_learning_unit.find_by_learning_unit_year(learning_unit_year).initial_data
    initial_learning_unit_year, learning_unit_year_fields = get_learning_unit_year_comparison_context(
        initial_data,
        learning_unit_year
    )
    components = get_components_identification(learning_unit_year)
    components_list = []
    for component in components['components']:
        volumes = get_volumes_comparison_context(component, initial_data)
        components_list.append(
            [
                _get_value_from_enum(LEARNING_COMPONENT_YEAR_TYPES, component['learning_component_year'].type),
                volumes
            ]
        )
    context = {
        'learning_unit_year': learning_unit_year,
        'learning_container_year_fields': get_learning_container_year_comparison_context(
            initial_data,
            learning_unit_year
        ),
        'campus': [
            learning_unit_year._meta.get_field('campus').verbose_name,
            initial_learning_unit_year.campus.name,
            learning_unit_year.campus.name] \
            if initial_learning_unit_year.campus.name != learning_unit_year.campus.name else [],
        'entities_fields': get_all_entities_comparison_context(initial_data, learning_unit_year),
        'learning_unit_year_fields': learning_unit_year_fields,
        'components': components_list
    }
    return render(request, "learning_unit/proposal_comparison.html", context)


def get_volumes_comparison_context(component, initial_data):
    volumes = {}
    component_type = component['learning_component_year'].type
    volume_total = component['volumes']['VOLUME_TOTAL'] or 0
    volume_q1 = component['volumes']['VOLUME_Q1'] or 0
    volume_q2 = component['volumes']['VOLUME_Q2'] or 0
    planned_classes = component['volumes']['PLANNED_CLASSES'] or 0
    if volume_total != initial_data['volumes'][component_type]['VOLUME_TOTAL']:
        volumes[_('Volume total annual')] = [initial_data['volumes'][component_type]['VOLUME_TOTAL'], volume_total]
    if planned_classes != initial_data['volumes'][component_type]['PLANNED_CLASSES']:
        volumes[_('Planned classes')] = [initial_data['volumes'][component_type]['PLANNED_CLASSES'],
                                         planned_classes]
    if volume_q1 != initial_data['volumes'][component_type]['VOLUME_Q1']:
        volumes[_('Volume Q1')] = [initial_data['volumes'][component_type]['VOLUME_Q1'], volume_q1]
    if volume_q2 != initial_data['volumes'][component_type]['VOLUME_Q2']:
        volumes[_('Volume Q2')] = [initial_data['volumes'][component_type]['VOLUME_Q2'], volume_q2]
    return volumes


def get_all_entities_comparison_context(initial_data, learning_unit_year):
    entities_fields = []
    for link_type in ENTITY_TYPE_LIST:
        link = EntityContainerYearLinkTypes[link_type].value
        new_entity = get_entity_by_type(learning_unit_year, link_type).most_recent_acronym if get_entity_by_type(
            learning_unit_year, link_type) else None
        initial_entity = entity.find_by_id(
            initial_data['entities'][link_type]).most_recent_acronym if entity.find_by_id(
            initial_data['entities'][link_type]) else None
        if initial_entity != new_entity:
            entities_fields.append([link, initial_entity, new_entity])
    return entities_fields


def get_learning_container_year_comparison_context(initial_data, learning_unit_year):
    initial_learning_container_year = deepcopy(learning_unit_year.learning_container_year)
    _reinitialize_model(initial_learning_container_year, initial_data["learning_container_year"])
    learning_container_year_fields = []
    for field in FIELDS_FOR_LEARNING_CONTAINER_YR_COMPARISON:
        if getattr(initial_learning_container_year, field) != getattr(learning_unit_year.learning_container_year,
                                                                      field):
            field_name = learning_unit_year.learning_container_year._meta.get_field(field).verbose_name
            if field == 'type_declaration_vacant':
                initial = _get_value_from_enum(DECLARATION_TYPE,
                                               getattr(initial_learning_container_year, field))
                new_value = _get_value_from_enum(DECLARATION_TYPE,
                                                 getattr(learning_unit_year.learning_container_year, field))
            else:
                initial = getattr(initial_learning_container_year, field)
                new_value = getattr(learning_unit_year.learning_container_year, field)
            learning_container_year_fields.append([field_name, initial, new_value])
    return learning_container_year_fields


def get_learning_unit_year_comparison_context(initial_data, learning_unit_year):
    initial_learning_unit_year = deepcopy(learning_unit_year)
    _reinitialize_model(initial_learning_unit_year, initial_data["learning_unit_year"])
    learning_unit_year_fields = []
    for field in FIELDS_FOR_LEARNING_UNIT_YR_COMPARISON:
        if getattr(initial_learning_unit_year, field) != getattr(learning_unit_year, field):
            field_name = learning_unit_year._meta.get_field(field).verbose_name
            if field == 'periodicity':
                initial = _get_value_from_enum(PERIODICITY_TYPES, getattr(initial_learning_unit_year, field))
                new_value = _get_value_from_enum(PERIODICITY_TYPES, getattr(learning_unit_year, field))
            elif field == 'attribution_procedure':
                initial = _get_value_from_enum(ATTRIBUTION_PROCEDURES, getattr(initial_learning_unit_year, field))
                new_value = _get_value_from_enum(ATTRIBUTION_PROCEDURES, getattr(learning_unit_year, field))
            else:
                initial = getattr(initial_learning_unit_year, field)
                new_value = getattr(learning_unit_year, field)
            learning_unit_year_fields.append([field_name, initial, new_value])
    return initial_learning_unit_year, learning_unit_year_fields


def learning_unit_comparison(request, learning_unit_year_id):
    learning_unit_year = get_object_or_404(
        LearningUnitYear.objects.all().select_related('learning_unit', 'learning_container_year',
                                                      'campus', 'campus__organization'), pk=learning_unit_year_id
    )
    previous_context = {}
    current_context = get_full_context(learning_unit_year)
    next_context = {}
    previous_academic_year = mdl.academic_year.find_academic_year_by_year(learning_unit_year.academic_year.year - 1)
    if previous_academic_year:
        previous_learning_unit_year = _get_learning_unit_year(previous_academic_year, learning_unit_year)
        previous_context = get_full_context(previous_learning_unit_year) if previous_learning_unit_year else {}
    next_academic_year = mdl.academic_year.find_academic_year_by_year(learning_unit_year.academic_year.year + 1)
    if next_academic_year:
        next_learning_unit_year = _get_learning_unit_year(next_academic_year, learning_unit_year)
        next_context = get_full_context(next_learning_unit_year) if next_learning_unit_year else {}
    context = build_context_comparison(current_context, learning_unit_year, next_context, previous_context)
    return render(request, "learning_unit/comparison.html", context)


def get_full_context(learning_unit_year):
    context = {'learning_unit_year': learning_unit_year}
    initial_data = None
    components_list = {}
    if proposal_learning_unit.is_learning_unit_year_in_proposal(learning_unit_year):
        initial_data = reinitialize_learning_unit_year(components_list, context, initial_data, learning_unit_year)
    context['learning_unit_year_fields'] = get_learning_unit_context(learning_unit_year)
    context['learning_container_year_fields'] = get_learning_container_year_context(learning_unit_year)
    context['campus'] = learning_unit_year.campus.name
    context['learning_container_year_partims'] = [partim.subdivision for partim in
                                                  learning_unit_year.get_partims_related()]
    context['entities_fields'] = get_entities_context(initial_data, learning_unit_year)
    if 'components' not in context:
        components = get_components_identification(learning_unit_year)
        for component in components['components']:
            volumes = {_('Volume total annual'): component['volumes']['VOLUME_TOTAL'] or 0,
                       _('Planned classes'): component['volumes']['PLANNED_CLASSES'] or 0,
                       _('Volume Q1'): component['volumes']['VOLUME_Q1'] or 0,
                       _('Volume Q2'): component['volumes']['VOLUME_Q2'] or 0}
            components_list[_get_value_from_enum(LEARNING_COMPONENT_YEAR_TYPES,
                                                 component['learning_component_year'].type)] = volumes
        context['components'] = components_list
    return context


def reinitialize_learning_unit_year(components_list, context, initial_data, learning_unit_year):
    initial_data = proposal_learning_unit.find_by_learning_unit_year(learning_unit_year).initial_data
    _reinitialize_model(learning_unit_year, initial_data["learning_unit_year"])
    _reinitialize_model(learning_unit_year.learning_container_year, initial_data["learning_container_year"])
    _reinitialize_components(initial_data["learning_component_years"] or {})
    for component in initial_data['learning_component_years']:
        volumes = {_('Volume total annual'): component['hourly_volume_total_annual'] or 0,
                   _('Planned classes'): component['planned_classes'] or 0,
                   _('Volume Q1'): component['hourly_volume_partial_q1'] or 0,
                   _('Volume Q2'): component['hourly_volume_partial_q2'] or 0}
        components_list[_get_value_from_enum(LEARNING_COMPONENT_YEAR_TYPES, component['type'])] = volumes
    context['components'] = components_list
    return initial_data


def get_entities_context(initial_data, learning_unit_year):
    entities_fields = {}
    for link_type in ENTITY_TYPE_LIST:
        link = EntityContainerYearLinkTypes[link_type].value
        if initial_data:
            entity_data = entity.find_by_id(
                initial_data['entities'][link_type]).most_recent_acronym if entity.find_by_id(
                initial_data['entities'][link_type]) else None
        else:
            entity_data = get_entity_by_type(learning_unit_year, link_type).most_recent_acronym if get_entity_by_type(
                learning_unit_year, link_type) else None
        entities_fields[link] = entity_data
    return entities_fields


def get_learning_container_year_context(learning_unit_year):
    learning_container_year_fields = {}
    for field in FIELDS_FOR_LEARNING_CONTAINER_YR_COMPARISON:
        field_name = learning_unit_year.learning_container_year._meta.get_field(field).verbose_name
        if field == 'type_declaration_vacant':
            value = _get_value_from_enum(DECLARATION_TYPE, getattr(learning_unit_year.learning_container_year, field))
        else:
            value = getattr(learning_unit_year.learning_container_year, field)
        learning_container_year_fields[field_name] = value
    return learning_container_year_fields


def get_learning_unit_context(learning_unit_year):
    learning_unit_year_fields = {}
    for field in FIELDS_FOR_LEARNING_UNIT_YR_COMPARISON:
        field_name = learning_unit_year._meta.get_field(field).verbose_name
        if field == 'periodicity':
            value = _get_value_from_enum(PERIODICITY_TYPES, getattr(learning_unit_year, field))
        elif field == 'attribution_procedure':
            value = _get_value_from_enum(ATTRIBUTION_PROCEDURES, getattr(learning_unit_year, field))
        else:
            value = getattr(learning_unit_year, field)
        learning_unit_year_fields[field_name] = value
    return learning_unit_year_fields


def build_context_comparison(current_context, learning_unit_year, next_context, previous_context):
    return {
        'learning_unit_year': learning_unit_year,
        'previous': previous_context or {},
        'current': current_context or {},
        'next': next_context or {}
    }


def _reinitialize_model(obj_model, attribute_initial_values):
    for attribute_name, attribute_value in attribute_initial_values.items():
        if attribute_name != "id":
            cleaned_initial_value = _clean_attribute_initial_value(attribute_name, attribute_value)
            setattr(obj_model, attribute_name, cleaned_initial_value)


def _clean_attribute_initial_value(attribute_name, attribute_value):
    clean_attribute_value = attribute_value
    if attribute_name == "campus":
        clean_attribute_value = campus.find_by_id(attribute_value)
    elif attribute_name == "language":
        clean_attribute_value = language.find_by_id(attribute_value)
    return clean_attribute_value


def _reinitialize_components(initial_components):
    for initial_data_by_model in initial_components:
        learning_component_year = mdl_learning_component_year.LearningComponentYear.objects.get(
            pk=initial_data_by_model.get('id')
        )
        for attribute_name, attribute_value in initial_data_by_model.items():
            if attribute_name != "id":
                cleaned_initial_value = _clean_attribute_initial_value(attribute_name, attribute_value)
                setattr(learning_component_year, attribute_name, cleaned_initial_value)


def _get_learning_unit_year(academic_yr, learning_unit_yr):
    learning_unit_years = mdl.learning_unit_year.search(learning_unit=learning_unit_yr.learning_unit,
                                                        academic_year_id=academic_yr.id)
    if learning_unit_years.exists():
        return learning_unit_years.first()
    return None


def get_charge_repartition_warning_messages(learning_container_year):
    total_charges_by_attribution_and_learning_subtype = AttributionChargeNew.objects \
        .filter(attribution__learning_container_year=learning_container_year) \
        .order_by("attribution__tutor", "attribution__function", "attribution__start_year") \
        .values("attribution__tutor", "attribution__tutor__person__first_name",
                "attribution__tutor__person__middle_name", "attribution__tutor__person__last_name",
                "attribution__function", "attribution__start_year",
                "learning_component_year__learning_unit_year__subtype") \
        .annotate(total_volume=Sum("allocation_charge"))

    charges_by_attribution = itertools.groupby(total_charges_by_attribution_and_learning_subtype,
                                               lambda rec: "{}_{}_{}".format(rec["attribution__tutor"],
                                                                             rec["attribution__start_year"],
                                                                             rec["attribution__function"]))
    msgs = []
    for attribution_key, charges in charges_by_attribution:
        charges = list(charges)
        subtype_key = "learning_component_year__learning_unit_year__subtype"
        full_total_charges = next(
            (charge["total_volume"] for charge in charges if charge[subtype_key] == learning_unit_year_subtypes.FULL),
            0)
        partim_total_charges = next(
            (charge["total_volume"] for charge in charges if charge[subtype_key] == learning_unit_year_subtypes.PARTIM),
            0)
        partim_total_charges = partim_total_charges or 0
        full_total_charges = full_total_charges or 0
        if partim_total_charges > full_total_charges:
            tutor_name = Person.get_str(charges[0]["attribution__tutor__person__first_name"],
                                        charges[0]["attribution__tutor__person__middle_name"],
                                        charges[0]["attribution__tutor__person__last_name"])
            tutor_name_with_function = "{} ({})".format(tutor_name,
                                                        getattr(Functions, charges[0]["attribution__function"]).value)
            msg = _("The sum of volumes for the partims for professor %(tutor)s is superior to the "
                    "volume of parent learning unit for this professor") % {"tutor": tutor_name_with_function}
            msgs.append(msg)
    return msgs


def get_specifications_context(learning_unit_year, request):
    user_language = mdl.person.get_user_interface_language(request.user)
    fr_language = find_language_in_settings(settings.LANGUAGE_CODE_FR)
    en_language = find_language_in_settings(settings.LANGUAGE_CODE_EN)
    return {
        'cms_specification_labels_translated': get_cms_label_data(CMS_LABEL_SPECIFICATIONS, user_language),
        'form_french': LearningUnitSpecificationsForm(learning_unit_year, fr_language),
        'form_english': LearningUnitSpecificationsForm(learning_unit_year, en_language)
    }


def get_languages_settings():
    return {
        'LANGUAGE_CODE_FR': settings.LANGUAGE_CODE_FR,
        'LANGUAGE_CODE_EN': settings.LANGUAGE_CODE_EN
    }
