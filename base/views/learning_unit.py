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
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods

from base import models as mdl
from attribution import models as mdl_attr
from base.models import entity_container_year
from base.models.enums import entity_container_year_link_type
from base.models.enums import learning_container_year_types
from cms import models as mdl_cms
from cms.enums import entity_name
from base.forms.learning_units import LearningUnitYearForm
from base.forms.learning_unit_specifications import LearningUnitSpecificationsForm
from base.forms.learning_unit_pedagogy import LearningUnitPedagogyForm, LearningUnitPedagogyEditForm
from base.models.enums import learning_unit_year_subtypes
from cms.models import text_label

from . import layout

UNDEFINED_VALUE = '?'

HOURLY_VOLUME_KEY = 'hourly_volume'
TOTAL_VOLUME_KEY = 'total_volume'
VOLUME_PARTIAL_KEY = 'volume_partial'
VOLUME_REMAINING_KEY = 'volume_remaining'

VOLUME_FOR_UNKNOWN_QUADRIMESTER = -1


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_units(request):
    if request.GET.get('academic_year'):
        form = LearningUnitYearForm(request.GET)
    else:
        form = LearningUnitYearForm()
    found_learning_units = None
    if form.is_valid():
        found_learning_units = form.get_learning_units()
        _check_if_display_message(request, learning_units)

    context = _get_common_context_list_learning_unit_years()
    context.update({
        'form': form,
        'academic_years': mdl.academic_year.find_academic_years(),
        'learning_units': found_learning_units,
        'current_academic_year': mdl.academic_year.current_academic_year(),
        'experimental_phase': True
    })
    return layout.render(request, "learning_units.html", context)


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
    context['components'] = get_components(learning_unit_year.learning_container_year, False)
    context['volume_distribution'] = volume_distribution(learning_unit_year.learning_container_year)

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
    context['components'] = get_components(context['learning_unit_year'].learning_container_year, True)
    context['tab_active'] = 'components'
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/components.html", context)


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


def _check_if_display_message(request, learning_units):
    if not learning_units:
        messages.add_message(request, messages.WARNING, _('no_result'))


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


def get_components(a_learning_container_yr, get_classes):
    components = []
    if a_learning_container_yr:
        learning_component_year_list = mdl.learning_component_year.find_by_learning_container_year(a_learning_container_yr)

        for learning_component_year in learning_component_year_list:
            if get_classes:
                learning_class_year_list = mdl.learning_class_year.find_by_learning_component_year(learning_component_year)
                learning_class_year_dict = dict()
                for learning_class_year in learning_class_year_list:
                    learning_unit_component_class = mdl.learning_unit_component_class.find_by_learning_class_year(learning_class_year)
                    learning_class_year_dict[learning_class_year] = learning_unit_component_class
            else:
                learning_class_year_dict = None
            entity_container_yrs = mdl.entity_container_year.find_by_learning_container_year(learning_component_year.learning_container_year,
                                                                                            entity_container_year_link_type.REQUIREMENT_ENTITY)
            entity_component_yr = mdl.entity_component_year.find_by_entity_container_years(entity_container_yrs,
                                                                                          learning_component_year).first()
            components.append({'learning_component_year': learning_component_year,
                               'entity_component_yr': entity_component_yr,
                               'volumes': volumes(entity_component_yr),
                               'classes': learning_class_year_dict})
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
        all_attributions = entity_container_year.find_entities(learning_unit_year.learning_container_year)
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


def volumes(entity_component_yr):
    if entity_component_yr:
        if not entity_component_yr.hourly_volume_total:
            return dict.fromkeys([HOURLY_VOLUME_KEY, TOTAL_VOLUME_KEY, VOLUME_PARTIAL_KEY, VOLUME_REMAINING_KEY],
                                 UNDEFINED_VALUE)

        if entity_component_yr.hourly_volume_partial is None:
            return {HOURLY_VOLUME_KEY: entity_component_yr.hourly_volume_total,
                    TOTAL_VOLUME_KEY: UNDEFINED_VALUE,
                    VOLUME_PARTIAL_KEY: UNDEFINED_VALUE,
                    VOLUME_REMAINING_KEY: UNDEFINED_VALUE}

        if unknown_volume_partial(entity_component_yr):
            return {HOURLY_VOLUME_KEY: entity_component_yr.hourly_volume_total,
                    TOTAL_VOLUME_KEY: 'partial_or_remaining',
                    VOLUME_PARTIAL_KEY: '({})'.format(entity_component_yr.hourly_volume_total),
                    VOLUME_REMAINING_KEY: '({})'.format(entity_component_yr.hourly_volume_total)}

        return {HOURLY_VOLUME_KEY: entity_component_yr.hourly_volume_total,
                TOTAL_VOLUME_KEY: format_nominal_volume(entity_component_yr),
                VOLUME_PARTIAL_KEY: entity_component_yr.hourly_volume_partial,
                VOLUME_REMAINING_KEY: format_volume_remaining(entity_component_yr)}


def unknown_volume_partial(entity_component_yr):
    return entity_component_yr.hourly_volume_partial == VOLUME_FOR_UNKNOWN_QUADRIMESTER


def format_nominal_volume(entity_component_yr):
    if entity_component_yr.hourly_volume_total == entity_component_yr.hourly_volume_partial:
        return 'partial'
    elif entity_component_yr.hourly_volume_partial == 0:
        return 'remaining'
    else:
        return 'partial_remaining'


def format_volume_remaining(entity_component_yr):
    volume_remaining = entity_component_yr.hourly_volume_total - entity_component_yr.hourly_volume_partial
    if volume_remaining == 0:
        return '-'
    return volume_remaining


def volume_distribution(a_learning_container_yr):

    component_partial_exists = False
    component_remaining_exists = False

    if a_learning_container_yr:
        learning_component_yrs = mdl.learning_component_year.find_by_learning_container_year(a_learning_container_yr)

        for learning_component_year in learning_component_yrs:
            entity_container_yrs = mdl.entity_container_year\
                .find_by_learning_container_year(learning_component_year.learning_container_year,
                                                 entity_container_year_link_type.REQUIREMENT_ENTITY)
            entity_component_yrs = mdl.entity_component_year\
                .find_by_entity_container_years(entity_container_yrs, learning_component_year)
            for entity_component_yr in entity_component_yrs:
                if entity_component_yr.hourly_volume_partial is None:
                    return UNDEFINED_VALUE
                else:
                    if entity_component_yr.hourly_volume_partial == entity_component_yr.hourly_volume_total:
                        component_partial_exists = True
                    if entity_component_yr.hourly_volume_partial == 0.00:
                        component_remaining_exists = True
                    if entity_component_yr.hourly_volume_partial == VOLUME_FOR_UNKNOWN_QUADRIMESTER:
                        return _('partial_or_remaining')
                    if entity_component_yr.hourly_volume_partial > 0.00 and entity_component_yr.hourly_volume_partial < entity_component_yr.hourly_volume_total:
                        return _('partial_remaining')

        if component_partial_exists:
            if component_remaining_exists:
                return _('partial_remaining')
            else:
                return _('partial')
        else:
            if component_remaining_exists:
                return _('remaining')

    return None

