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

from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.utils.translation import ugettext_lazy as _

from base import models as mdl
from attribution import models as mdl_attr
from base.models.enums import learning_container_year_types
from cms import models as mdl_cms
from cms.enums import entity_name
from base.forms.learning_units import LearningUnitYearForm
from base.forms.learning_unit_specifications import LearningUnitSpecificationsForm
from base.forms.learning_unit_pedagogy import LearningUnitPedagogyForm

from . import layout


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
    context['components'] = get_components(context['learning_unit_year'].learning_container_year)
    context['tab_active'] = 'components'
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/components.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_pedagogy(request, learning_unit_year_id):
    context = _get_common_context_learning_unit_year(learning_unit_year_id)
    learning_unit_year = context['learning_unit_year']
    user_language = mdl.person.get_user_interface_language(request.user)

    CMS_LABEL = ['resume', 'bibliography', 'teaching_methods', 'evaluation_methods',
                 'other_informations', 'online_resources']
    translated_labels = mdl_cms.translated_text_label.search(text_entity=entity_name.LEARNING_UNIT_YEAR,
                                                             labels=CMS_LABEL,
                                                             language=user_language)

    fr_language = next((lang for lang in settings.LANGUAGES if lang[0] == 'fr-be'), None)
    en_language = next((lang for lang in settings.LANGUAGES if lang[0] == 'en'), None)
    for trans_label in translated_labels:
        label_name = trans_label.text_label.label
        context[label_name] = trans_label.label

    context.update({
        'form_french': LearningUnitPedagogyForm(learning_unit_year, fr_language),
        'form_english': LearningUnitPedagogyForm(learning_unit_year, en_language)
    })
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/pedagogy.html", context)


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
    user_language = mdl.person.get_user_interface_language(request.user)

    CMS_LABEL = ['themes_discussed', 'skills_to_be_acquired', 'prerequisite']
    translated_labels = mdl_cms.translated_text_label.search(text_entity=entity_name.LEARNING_UNIT_YEAR,
                                                             labels=CMS_LABEL,
                                                             language=user_language)

    fr_language = next((lang for lang in settings.LANGUAGES if lang[0] == 'fr-be'), None)
    en_language = next((lang for lang in settings.LANGUAGES if lang[0] == 'en'), None)
    for trans_label in translated_labels:
        label_name = trans_label.text_label.label
        context[label_name] = trans_label.label

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


def get_components(a_learning_container_yr):
    components = []
    if a_learning_container_yr:
        learning_component_year_list = mdl.learning_component_year.find_by_learning_container_year(a_learning_container_yr)

        for learning_component_year in learning_component_year_list:
            learning_class_year_list = mdl.learning_class_year.find_by_learning_component_year(learning_component_year)
            components.append({'learning_component_year': learning_component_year,
                               'classes': learning_class_year_list})
    return components


def _get_partims_related(learning_unit_year):
    learning_container_year = learning_unit_year.learning_container_year
    return mdl.learning_container_year.find_all_partims(learning_container_year)


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