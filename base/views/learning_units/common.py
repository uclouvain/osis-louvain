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

from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from base import models as mdl
from base.business.learning_unit import get_organization_from_learning_unit_year, get_all_attributions, \
    get_components_identification
from base.business.learning_unit_proposal import get_difference_of_proposal
from base.business.learning_units.edition import create_learning_unit_year_creation_message
from base.business.learning_units.perms import learning_unit_year_permissions, learning_unit_proposal_permissions, \
    is_eligible_to_create_partim
from base.models import proposal_learning_unit
from base.models.learning_unit import REGEX_BY_SUBTYPE
from base.models.learning_unit_year import LearningUnitYear
from base.views.common import display_success_messages
from osis_common.decorators.ajax import ajax_required


def show_success_learning_unit_year_creation_message(request, learning_unit_year_created, translation_key):
    success_msg = create_learning_unit_year_creation_message(learning_unit_year_created, translation_key)
    display_success_messages(request, success_msg, extra_tags='safe')


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


def get_learning_unit_identification_context(learning_unit_year_id, person):
    context = get_common_context_learning_unit_year(learning_unit_year_id, person)

    learning_unit_year = context['learning_unit_year']
    context['warnings'] = learning_unit_year.warnings
    proposal = proposal_learning_unit.find_by_learning_unit(learning_unit_year.learning_unit)

    context["can_create_partim"] = is_eligible_to_create_partim(learning_unit_year, person)
    context['learning_container_year_partims'] = learning_unit_year.get_partims_related()
    context['organization'] = get_organization_from_learning_unit_year(learning_unit_year)
    context['campus'] = learning_unit_year.campus
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


def get_common_context_learning_unit_year(learning_unit_year_id, person):
    query_set = LearningUnitYear.objects.all().select_related('learning_unit', 'learning_container_year')
    learning_unit_year = get_object_or_404(query_set, pk=learning_unit_year_id)
    return {
        'learning_unit_year': learning_unit_year,
        'current_academic_year': mdl.academic_year.current_academic_year(),
        'is_person_linked_to_entity': person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year),
        'experimental_phase': True
    }


def get_text_label_translated(text_lb, user_language):
    return next((txt for txt in text_lb.translated_text_labels
                 if txt.language == user_language), None)
