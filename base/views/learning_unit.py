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
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Prefetch
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _, get_language
from django.views.decorators.http import require_http_methods

from base import models as mdl
from base.business.learning_unit import get_cms_label_data, \
    get_same_container_year_components, CMS_LABEL_SPECIFICATIONS, get_achievements_group_by_language, \
    get_components_identification
from base.business.learning_unit_proposal import _get_value_from_enum, clean_attribute_initial_value
from base.business.learning_units import perms as business_perms
from base.business.learning_units.comparison import FIELDS_FOR_LEARNING_UNIT_YR_COMPARISON, \
    FIELDS_FOR_LEARNING_CONTAINER_YR_COMPARISON
from base.business.learning_units.perms import can_update_learning_achievement
from base.enums.component_detail import VOLUME_TOTAL, VOLUME_Q1, VOLUME_Q2, PLANNED_CLASSES, \
    VOLUME_REQUIREMENT_ENTITY, VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1, VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2
from base.forms.learning_unit_specifications import LearningUnitSpecificationsForm, LearningUnitSpecificationsEditForm
from base.models import education_group_year, proposal_learning_unit
from base.models import learning_component_year as mdl_learning_component_year
from base.models.entity_version import EntityVersion
from base.models.enums.attribution_procedure import ATTRIBUTION_PROCEDURES
from base.models.enums.entity_container_year_link_type import EntityContainerYearLinkTypes
from base.models.enums.learning_component_year_type import LEARNING_COMPONENT_YEAR_TYPES
from base.models.enums.learning_unit_year_periodicity import PERIODICITY_TYPES
from base.models.enums.vacant_declaration_type import DECLARATION_TYPE
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.models.proposal_learning_unit import ProposalLearningUnit
from base.views.common import display_success_messages
from base.views.learning_units.common import get_common_context_learning_unit_year, get_text_label_translated
from cms.models.text_label import TextLabel
from cms.models.translated_text_label import TranslatedTextLabel
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
    formations_by_educ_group_year = mdl.group_element_year.find_learning_unit_roots(
        education_groups_years,
        return_result_params={
            'parents_as_instances': True,
            'with_parents_of_parents': True
        },
        luy=learn_unit_year
    )
    context['formations_by_educ_group_year'] = formations_by_educ_group_year
    context['group_elements_years'] = group_elements_years

    context['root_formations'] = education_group_year.find_with_enrollments_count(learn_unit_year)
    context['total_formation_enrollments'] = 0
    context['total_learning_unit_enrollments'] = 0
    for root_formation in context['root_formations']:
        context['total_formation_enrollments'] += root_formation.count_formation_enrollments
        context['total_learning_unit_enrollments'] += root_formation.count_learning_unit_enrollments
    context['tab_active'] = "learning_unit_formations"  # Corresponds to url_name
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
    context['tab_active'] = 'learning_unit_components'  # Corresponds to url_name
    return render(request, "learning_unit/components.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_specifications(request, learning_unit_year_id):
    person = get_object_or_404(Person, user=request.user)
    context = get_common_context_learning_unit_year(learning_unit_year_id, person)
    learning_unit_year = context['learning_unit_year']

    context.update(get_specifications_context(learning_unit_year, request))
    context.update(get_achievements_group_by_language(learning_unit_year))
    context.update(get_languages_settings())
    context["achievements"] = list(itertools.zip_longest(
        context.get("achievements_FR", []),
        context.get("achievements_EN", [])
    ))
    context['can_update_learning_achievement'] = can_update_learning_achievement(learning_unit_year, person)
    context['tab_active'] = 'learning_unit_specifications'  # Corresponds to url_name
    return render(request, "learning_unit/specifications.html", context)


@login_required
@permission_required('base.can_edit_learningunit_specification', raise_exception=True)
@require_http_methods(["GET", "POST"])
def learning_unit_specifications_edit(request, learning_unit_year_id):
    if request.method == 'POST':
        form = LearningUnitSpecificationsEditForm(request.POST)
        if form.is_valid():
            field_label, last_academic_year = form.save()
            display_success_messages(
                request,
                build_success_message(last_academic_year, learning_unit_year_id, form.postponement)
            )
        return HttpResponse()
    else:
        context = get_common_context_learning_unit_year(learning_unit_year_id,
                                                        get_object_or_404(Person, user=request.user))
        label_name = request.GET.get('label')
        text_lb = TextLabel.objects.prefetch_related(
            Prefetch('translatedtextlabel_set', to_attr="translated_text_labels")
        ).get(label=label_name)
        form = LearningUnitSpecificationsEditForm(**{
            'learning_unit_year': context['learning_unit_year'],
            'text_label': text_lb
        })
        form.load_initial()  # Load data from database
        context['form'] = form
        context['text_label_translated'] = get_text_label_translated(text_lb, get_language())
        return render(request, "learning_unit/specifications_edit.html", context)


def _get_cms_label_translated(cms_label, user_language):
    return TranslatedTextLabel.objects.filter(
        text_label=cms_label,
        language=user_language
    ).first().label


def build_success_message(last_academic_year=None, learning_unit_year_id=None, with_postponement=False):
    default_msg = _("The learning unit has been updated")
    luy = LearningUnitYear.objects.get(id=learning_unit_year_id)
    proposal = ProposalLearningUnit.objects.filter(
        learning_unit_year__learning_unit=luy.learning_unit
    ).first()

    if not proposal and last_academic_year:
        msg = "{} {}.".format(
            default_msg, _("and postponed until %(year)s") % {
                'year': last_academic_year
            }
        )
    elif proposal and proposal_is_on_same_year(proposal=proposal, base_luy=luy):
        msg = "{}. {}.".format(
            default_msg,
            _("The learning unit is in proposal, the report from %(proposal_year)s will be done at consolidation") % {
                'proposal_year': proposal.learning_unit_year.academic_year
            }
        )
    elif proposal and proposal_is_on_future_year(proposal=proposal, base_luy=luy) and with_postponement:
        msg = _("The learning unit has been updated (the report has not been done from %(year)s because the "
                "learning unit is in proposal).") % {
                  'year': proposal.learning_unit_year.academic_year
              }

    elif proposal and proposal_is_on_future_year(proposal=proposal, base_luy=luy) and not with_postponement:
        msg = "{} ({}).".format(
            default_msg,
            _("without postponement")
        )

    else:
        msg = "{}.".format(default_msg)

    return msg


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
            learning_unit_year.campus.name] if initial_learning_unit_year.campus.name != learning_unit_year.campus.name
        else [],
        'entities_fields': get_all_entities_comparison_context(initial_data, learning_unit_year),
        'learning_unit_year_fields': learning_unit_year_fields,
        'components': components_list
    }
    return render(request, "learning_unit/proposal_comparison.html", context)


def get_volumes_comparison_context(component, initial_data):
    volumes = {}
    acronym = component['learning_component_year'].acronym
    repartition_volume_total = component['volumes'][VOLUME_TOTAL] or 0
    repartition_volume_q1 = component['volumes'][VOLUME_Q1] or 0
    repartition_volume_q2 = component['volumes'][VOLUME_Q2] or 0
    planned_classes = component['volumes'][PLANNED_CLASSES] or 0
    repartition_volume_requirement_entity = component['volumes'][VOLUME_REQUIREMENT_ENTITY] or 0
    repartition_volume_additional_entity_1 = component['volumes'][VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1] or 0
    repartition_volume_additional_entity_2 = component['volumes'][VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2] or 0
    initial_volume_total = initial_data['volumes'][acronym][VOLUME_TOTAL] or 0
    initial_volume_q1 = initial_data['volumes'][acronym][VOLUME_Q1] or 0
    initial_volume_q2 = initial_data['volumes'][acronym][VOLUME_Q2] or 0
    initial_planned_classes = initial_data['volumes'][acronym][PLANNED_CLASSES] or 0
    initial_volume_requirement_entity = initial_data['volumes'][acronym][VOLUME_REQUIREMENT_ENTITY] or 0
    initial_volume_additional_entity_1 = initial_data['volumes'][acronym][VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1] or 0
    initial_volume_additional_entity_2 = initial_data['volumes'][acronym][VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2] or 0
    if repartition_volume_total != initial_volume_total:
        volumes[_('Volume total annual')] = [Decimal(initial_volume_total), Decimal(repartition_volume_total)]
    if planned_classes != initial_planned_classes:
        volumes[_('Planned classes')] = [initial_planned_classes, planned_classes]
    if repartition_volume_q1 != initial_volume_q1:
        volumes[_('Volume Q1')] = [Decimal(initial_volume_q1), Decimal(repartition_volume_q1)]
    if repartition_volume_q2 != initial_volume_q2:
        volumes[_('Volume Q2')] = [Decimal(initial_volume_q2), Decimal(repartition_volume_q2)]
    if repartition_volume_requirement_entity != initial_volume_requirement_entity:
        volumes[_('Requirement entity')] = [Decimal(initial_volume_requirement_entity),
                                            Decimal(repartition_volume_requirement_entity)]
    if repartition_volume_additional_entity_1 != initial_volume_additional_entity_1:
        volumes[_('Additional requirement entity 1')] = [Decimal(initial_volume_additional_entity_1),
                                                         Decimal(repartition_volume_additional_entity_1)]
    if repartition_volume_additional_entity_2 != initial_volume_additional_entity_2:
        volumes[_('Additional requirement entity 2')] = [Decimal(initial_volume_additional_entity_2),
                                                         Decimal(repartition_volume_additional_entity_2)]
    return volumes


def get_all_entities_comparison_context(initial_data, learning_unit_year):
    entities_fields = []
    new_container_year = learning_unit_year.learning_container_year
    for entity_link, attr in new_container_year.get_attrs_by_entity_container_type().items():
        new_entity = getattr(new_container_year, attr, None)
        new_entity_acronym = new_entity.most_recent_acronym if new_entity else None
        initial_entity_acronym = _get_initial_entity_acronym(initial_data, attr)
        if initial_entity_acronym != new_entity_acronym:
            translated_value = EntityContainerYearLinkTypes[entity_link].value
            entities_fields.append([translated_value, initial_entity_acronym, new_entity_acronym])
    return entities_fields


def _get_initial_entity_acronym(initial_data, entity_key_field_name):
    initial_entity_acronym = None
    initial_entity_id = initial_data['learning_container_year'][entity_key_field_name]
    if initial_entity_id:
        now = timezone.now().date()
        initial_entity_acronym = EntityVersion.objects.current(now).get(entity_id=initial_entity_id).acronym
    return initial_entity_acronym


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
            elif field == 'credits':
                initial = Decimal(getattr(initial_learning_unit_year, field))
                new_value = Decimal(getattr(learning_unit_year, field))
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
        get_component_values(components, components_list)
        context['components'] = components_list
    return context


def get_component_values(components, components_list):
    for component in components['components']:
        volumes = {
            _('Volume total annual'): component['volumes'][VOLUME_TOTAL] or 0,
            _('Planned classes'): component['volumes'][PLANNED_CLASSES] or 0,
            _('Volume Q1'): component['volumes'][VOLUME_Q1] or 0,
            _('Volume Q2'): component['volumes'][VOLUME_Q2] or 0,
            _('Requirement entity'): component['volumes'][VOLUME_REQUIREMENT_ENTITY] or 0,
            _('Additional requirement entity 1'): component['volumes'][VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_1] or 0,
            _('Additional requirement entity 2'): component['volumes'][VOLUME_ADDITIONAL_REQUIREMENT_ENTITY_2] or 0
        }
        components_list[_get_value_from_enum(LEARNING_COMPONENT_YEAR_TYPES,
                                             component['learning_component_year'].type)] = volumes


def reinitialize_learning_unit_year(components_list, context, initial_data, learning_unit_year):
    initial_data = proposal_learning_unit.find_by_learning_unit_year(learning_unit_year).initial_data
    _reinitialize_model(learning_unit_year, initial_data["learning_unit_year"])
    _reinitialize_model(learning_unit_year.learning_container_year, initial_data["learning_container_year"])
    _reinitialize_components(initial_data["learning_component_years"] or {})
    for component in initial_data['learning_component_years']:
        volumes = {_('Volume total annual'): component['hourly_volume_total_annual'] or 0,
                   _('Planned classes'): component['planned_classes'] or 0,
                   _('Volume Q1'): component['hourly_volume_partial_q1'] or 0,
                   _('Volume Q2'): component['hourly_volume_partial_q2'] or 0,
                   _('Requirement entity'): component['repartition_volume_requirement_entity'] or 0,
                   _('Additional requirement entity 1'): component['repartition_volume_additional_entity_1'] or 0,
                   _('Additional requirement entity 2'): component['repartition_volume_additional_entity_2'] or 0
                   }
        components_list[_get_value_from_enum(LEARNING_COMPONENT_YEAR_TYPES, component['type'])] = volumes
    context['components'] = components_list
    return initial_data


def get_entities_context(initial_data, learning_unit_year):
    entities_fields = {}
    container_year = learning_unit_year.learning_container_year
    for entity_link, attr in container_year.get_attrs_by_entity_container_type().items():
        if initial_data:
            entity_acronym = _get_initial_entity_acronym(initial_data, attr)
        else:
            entity_acronym = container_year.get_most_recent_entity_acronym(entity_link)
        translated_value = EntityContainerYearLinkTypes[entity_link].value
        entities_fields[translated_value] = entity_acronym
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
            cleaned_initial_value = clean_attribute_initial_value(attribute_name, attribute_value)
            setattr(obj_model, attribute_name, cleaned_initial_value)


def _reinitialize_components(initial_components):
    for initial_data_by_model in initial_components:
        learning_component_year = mdl_learning_component_year.LearningComponentYear.objects.get(
            pk=initial_data_by_model.get('id')
        )
        for attribute_name, attribute_value in initial_data_by_model.items():
            if attribute_name != "id":
                cleaned_initial_value = clean_attribute_initial_value(attribute_name, attribute_value)
                setattr(learning_component_year, attribute_name, cleaned_initial_value)


def _get_learning_unit_year(academic_yr, learning_unit_yr):
    learning_unit_years = mdl.learning_unit_year.search(learning_unit=learning_unit_yr.learning_unit,
                                                        academic_year_id=academic_yr.id)
    if learning_unit_years.exists():
        return learning_unit_years.first()
    return None


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


def proposal_is_on_future_year(proposal, base_luy):
    return proposal.learning_unit_year.academic_year.year > base_luy.academic_year.year


def proposal_is_on_same_year(proposal, base_luy):
    return proposal.learning_unit_year.academic_year.year == base_luy.academic_year.year
