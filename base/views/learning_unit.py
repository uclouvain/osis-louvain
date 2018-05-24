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
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_http_methods

from attribution.business import attribution_charge_new
from base import models as mdl
from base.business.learning_unit import get_cms_label_data, \
    get_same_container_year_components, get_components_identification, get_organization_from_learning_unit_year, \
    get_campus_from_learning_unit_year, \
    get_all_attributions, find_language_in_settings, \
    CMS_LABEL_SPECIFICATIONS, get_achievements_group_by_language
from base.business.learning_unit_proposal import get_difference_of_proposal
from base.business.learning_units import perms as business_perms
from base.business.learning_units.perms import learning_unit_year_permissions, learning_unit_proposal_permissions, \
    can_update_learning_achievement
from base.forms.learning_class import LearningClassEditForm
from base.forms.learning_unit.learning_unit_create_2 import FullForm, PartimForm
from base.forms.learning_unit.learning_unit_postponement import LearningUnitPostponementForm
from base.forms.learning_unit_component import LearningUnitComponentEditForm
from base.forms.learning_unit_pedagogy import LearningUnitPedagogyEditForm
from base.forms.learning_unit_specifications import LearningUnitSpecificationsForm, LearningUnitSpecificationsEditForm
from base.models import proposal_learning_unit, education_group_year
from base.models.academic_year import AcademicYear
from base.models.enums import learning_unit_year_subtypes
from base.models.learning_unit import REGEX_BY_SUBTYPE
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import Person
from base.views.learning_units import perms
from base.views.learning_units.common import show_success_learning_unit_year_creation_message
from cms.models import text_label
from osis_common.decorators.ajax import ajax_required
from . import layout


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_identification(request, learning_unit_year_id):
    person = get_object_or_404(Person, user=request.user)
    context = get_learning_unit_identification_context(learning_unit_year_id, person)
    return layout.render(request, "learning_unit/identification.html", context)


def get_common_context_learning_unit_year(learning_unit_year_id, person):
    query_set = LearningUnitYear.objects.all().select_related('learning_unit', 'learning_container_year')
    learning_unit_year = get_object_or_404(query_set, pk=learning_unit_year_id)
    return {
        'learning_unit_year': learning_unit_year,
        'current_academic_year': mdl.academic_year.current_academic_year(),
        'is_person_linked_to_entity': person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year),
        'experimental_phase': True
    }


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_formations(request, learning_unit_year_id):
    context = get_common_context_learning_unit_year(learning_unit_year_id, get_object_or_404(Person, user=request.user))
    learn_unit_year = context["learning_unit_year"]
    group_elements_years = mdl.group_element_year.search(child_leaf=learn_unit_year) \
        .select_related("parent", "child_leaf").order_by('parent__partial_acronym')
    education_groups_years = [group_element_year.parent for group_element_year in group_elements_years]
    formations_by_educ_group_year = mdl.group_element_year.find_learning_unit_formations(education_groups_years,
                                                                                         parents_as_instances=True)
    context['formations_by_educ_group_year'] = formations_by_educ_group_year
    context['group_elements_years'] = group_elements_years

    context['root_formations'] = education_group_year.find_with_enrollments_count(learn_unit_year)

    return layout.render(request, "learning_unit/formations.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_components(request, learning_unit_year_id):
    person = get_object_or_404(Person, user=request.user)
    context = get_common_context_learning_unit_year(learning_unit_year_id, person)
    data_components = get_same_container_year_components(context['learning_unit_year'], True)
    context['components'] = data_components.get('components')
    context['REQUIREMENT_ENTITY'] = data_components.get('REQUIREMENT_ENTITY')
    context['ADDITIONAL_REQUIREMENT_ENTITY_1'] = data_components.get('ADDITIONAL_REQUIREMENT_ENTITY_1')
    context['ADDITIONAL_REQUIREMENT_ENTITY_2'] = data_components.get('ADDITIONAL_REQUIREMENT_ENTITY_2')
    context['tab_active'] = 'components'
    context['can_manage_volume'] = business_perms.is_eligible_for_modification(context["learning_unit_year"],
                                                                               person)
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/components.html", context)


@login_required
@permission_required('base.can_edit_learningunit_pedagogy', raise_exception=True)
@require_http_methods(["GET", "POST"])
def learning_unit_pedagogy_edit(request, learning_unit_year_id):
    redirect_url = reverse("learning_unit_pedagogy", kwargs={'learning_unit_year_id': learning_unit_year_id})
    return edit_learning_unit_pedagogy(request, learning_unit_year_id, redirect_url)


def edit_learning_unit_pedagogy(request, learning_unit_year_id, redirect_url):
    if request.method == 'POST':
        form = LearningUnitPedagogyEditForm(request.POST)
        if form.is_valid():
            form.save()
        return redirect(redirect_url)
    context = get_common_context_learning_unit_year(learning_unit_year_id,
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
    context = get_common_context_learning_unit_year(learning_unit_year_id,
                                                    get_object_or_404(Person, user=request.user))
    context['attribution_charge_news'] = \
        attribution_charge_new.find_attribution_charge_new_by_learning_unit_year(
            learning_unit_year=learning_unit_year_id)
    context['experimental_phase'] = True
    return layout.render(request, "learning_unit/attributions.html", context)


@login_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def learning_unit_specifications(request, learning_unit_year_id):
    person = get_object_or_404(Person, user=request.user)
    context = get_common_context_learning_unit_year(learning_unit_year_id, person)
    learning_unit_year = context['learning_unit_year']

    user_language = mdl.person.get_user_interface_language(request.user)
    context['cms_labels_translated'] = get_cms_label_data(CMS_LABEL_SPECIFICATIONS, user_language)

    fr_language = find_language_in_settings(settings.LANGUAGE_CODE_FR)
    en_language = find_language_in_settings(settings.LANGUAGE_CODE_EN)

    context.update({
        'form_french': LearningUnitSpecificationsForm(learning_unit_year, fr_language),
        'form_english': LearningUnitSpecificationsForm(learning_unit_year, en_language)
    })

    context.update(get_achievements_group_by_language(learning_unit_year))
    context.update({'LANGUAGE_CODE_FR': settings.LANGUAGE_CODE_FR, 'LANGUAGE_CODE_EN': settings.LANGUAGE_CODE_EN})
    context['can_update_learning_achievement'] = can_update_learning_achievement(learning_unit_year, person)
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

    context = get_common_context_learning_unit_year(learning_unit_year_id,
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
    context = get_common_context_learning_unit_year(learning_unit_year_id,
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
    context = get_common_context_learning_unit_year(learning_unit_year_id,
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
def learning_unit_create(request, academic_year_id):
    person = get_object_or_404(Person, user=request.user)
    if request.POST.get('academic_year'):
        academic_year_id = request.POST.get('academic_year')

    academic_year = get_object_or_404(AcademicYear, pk=academic_year_id)
    postponement_form = LearningUnitPostponementForm(
        person=person,
        start_postponement=academic_year,
        data=request.POST or None
    )
    if postponement_form.is_valid():
        new_luys = postponement_form.save()
        for luy in new_luys:
            show_success_learning_unit_year_creation_message(request, luy, 'learning_unit_successfuly_created')
        return redirect('learning_unit', learning_unit_year_id=new_luys[0].pk)
    return render(request, "learning_unit/simple/creation.html", postponement_form.get_context())


@login_required
@ajax_required
@permission_required('base.can_access_learningunit', raise_exception=True)
def check_acronym(request, subtype):
    acronym = request.GET['acronym']
    academic_yr = mdl.academic_year.find_academic_year_by_id(request.GET['year_id'])
    existed_acronym = False
    existing_acronym = False
    first_using = ""
    last_using = ""
    learning_unit_year = mdl.learning_unit_year.find_gte_year_acronym(academic_yr, acronym).first()
    old_learning_unit_year = mdl.learning_unit_year.find_lt_year_acronym(academic_yr, acronym).last()
    # FIXME there is the same check in the models
    if old_learning_unit_year:
        last_using = str(old_learning_unit_year.academic_year)
        existed_acronym = True

    if learning_unit_year:
        first_using = str(learning_unit_year.academic_year)
        existing_acronym = True

    if subtype not in REGEX_BY_SUBTYPE:
        valid = False
    else:
        valid = bool(re.match(REGEX_BY_SUBTYPE[subtype], acronym))

    return JsonResponse({'valid': valid, 'existing_acronym': existing_acronym, 'existed_acronym': existed_acronym,
                         'first_using': first_using, 'last_using': last_using}, safe=False)


@login_required
def outside_period(request):
    text = _('summary_responsible_denied')
    messages.add_message(request, messages.WARNING, "%s" % text)
    return render(request, "access_denied.html")


@login_required
@permission_required('base.can_create_learningunit', raise_exception=True)
@require_http_methods(["POST", "GET"])
@perms.can_create_partim
def create_partim_form(request, learning_unit_year_id):
    person = get_object_or_404(Person, user=request.user)
    learning_unit_year_full = get_object_or_404(LearningUnitYear, pk=learning_unit_year_id)

    postponement_form = LearningUnitPostponementForm(
        person=person,
        learning_unit_full_instance=learning_unit_year_full.learning_unit,
        start_postponement=learning_unit_year_full.academic_year,
        data=request.POST or None
    )

    if postponement_form.is_valid():
        new_luys = postponement_form.save()
        for luy in new_luys:
            show_success_learning_unit_year_creation_message(request, luy, 'learning_unit_successfuly_created')
        return redirect('learning_unit', learning_unit_year_id=new_luys[0].pk)
    return render(request, "learning_unit/simple/creation_partim.html", postponement_form.get_context())


def get_learning_unit_identification_context(learning_unit_year_id, person):
    context = get_common_context_learning_unit_year(learning_unit_year_id, person)

    learning_unit_year = context['learning_unit_year']
    if learning_unit_year.subtype == learning_unit_year_subtypes.FULL:
        context['warnings'] = FullForm(person, learning_unit_year.academic_year,
                                       learning_unit_instance=learning_unit_year.learning_unit).warnings
    else:
        context['warnings'] = PartimForm(person,
                                         learning_unit_full_instance=learning_unit_year.parent.learning_unit,
                                         academic_year=learning_unit_year.academic_year,
                                         learning_unit_instance=learning_unit_year.learning_unit).warnings
    proposal = proposal_learning_unit.find_by_learning_unit(learning_unit_year.learning_unit)

    context['learning_container_year_partims'] = learning_unit_year.get_partims_related()
    context['organization'] = get_organization_from_learning_unit_year(learning_unit_year)
    context['campus'] = get_campus_from_learning_unit_year(learning_unit_year)
    context['experimental_phase'] = True
    context.update(get_all_attributions(learning_unit_year))
    components = get_components_identification(learning_unit_year)
    context['components'] = components.get('components')
    context['REQUIREMENT_ENTITY'] = components.get('REQUIREMENT_ENTITY')
    context['ADDITIONAL_REQUIREMENT_ENTITY_1'] = components.get('ADDITIONAL_REQUIREMENT_ENTITY_1')
    context['ADDITIONAL_REQUIREMENT_ENTITY_2'] = components.get('ADDITIONAL_REQUIREMENT_ENTITY_2')
    context['proposal'] = proposal
    context['proposal_folder_entity_version'] = mdl.entity_version.get_by_entity_and_date(
        proposal.entity, None) if proposal else None
    context['differences'] = get_difference_of_proposal(proposal.initial_data, learning_unit_year) \
        if proposal and proposal.learning_unit_year == learning_unit_year \
        else {}

    # append permissions
    context.update(learning_unit_year_permissions(learning_unit_year, person))
    context.update(learning_unit_proposal_permissions(proposal, person, learning_unit_year))

    return context
