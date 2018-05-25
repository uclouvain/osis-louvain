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

from django import forms
from django.db import transaction
from django.db.models import Prefetch
from django.urls import reverse
from django.utils.functional import lazy
from django.utils.translation import ugettext_lazy as _

from base import models as mdl
from base.business.learning_unit_year_with_context import append_latest_entities
from base.forms.learning_unit import search_form as learning_units_form
from base.forms.common import get_clean_data, TooManyResultsException
from base.forms.learning_unit.search_form import SearchForm
from base.models import entity_version
from base.models.enums import entity_container_year_link_type, proposal_type, proposal_state
from base.models.proposal_learning_unit import ProposalLearningUnit


def _get_entity_folder_id_ordered_by_acronym():
    entities = mdl.proposal_learning_unit.find_distinct_folder_entities()
    entities_sorted_by_acronym = sorted(list(entities), key=lambda t: t.most_recent_acronym)

    return [SearchForm.ALL_LABEL] + [(ent.pk, ent.most_recent_acronym) for ent in entities_sorted_by_acronym]


def _get_sorted_choices(tuple_of_choices):
    return SearchForm.ALL_CHOICES + tuple(sorted(tuple_of_choices, key=lambda item: item[1]))


class LearningUnitProposalForm(SearchForm):

    entity_folder_id = forms.ChoiceField(
        label=_('folder_entity'),
        choices=lazy(_get_entity_folder_id_ordered_by_acronym, list),
        required=False
    )

    folder_id = forms.IntegerField(min_value=0,
                                   required=False,
                                   label=_('folder_num'),)

    proposal_type = forms.ChoiceField(
        label=_('proposal_type'),
        choices=_get_sorted_choices(proposal_type.CHOICES),
        required=False
    )

    proposal_state = forms.ChoiceField(
        label=_('proposal_status'),
        choices=_get_sorted_choices(proposal_state.CHOICES),
        required=False
    )

    def is_valid(self):
        if not super().is_valid():
            return False

        if not self._has_criteria():
            self.add_error(None, _('minimum_one_criteria'))
            return False
        return True

    def _has_criteria(self):
        criteria_present = False
        for name, field in self.fields.items():
            if self.cleaned_data[name]:
                criteria_present = True
                break
        return criteria_present

    def clean(self):
        if self.cleaned_data \
                and mdl.proposal_learning_unit.count_search_results(**self.cleaned_data) > SearchForm.MAX_RECORDS:
            raise TooManyResultsException
        return get_clean_data(self.cleaned_data)

    def get_proposal_learning_units(self):
        clean_data = self.cleaned_data

        entity_version_prefetch = Prefetch('entity__entityversion_set',
                                           queryset=mdl.entity_version.search(),
                                           to_attr='entity_versions')

        entity_container_prefetch = Prefetch('learning_unit_year__learning_container_year__entitycontaineryear_set',
                                             queryset=mdl.entity_container_year.search(
                                                 link_type=[entity_container_year_link_type.ALLOCATION_ENTITY,
                                                            entity_container_year_link_type.REQUIREMENT_ENTITY])
                                             .prefetch_related(entity_version_prefetch),
                                             to_attr='entity_containers_year')

        clean_data['learning_container_year_id'] = learning_units_form.get_filter_learning_container_ids(clean_data)

        proposal = mdl.proposal_learning_unit.search(**clean_data) \
            .select_related('learning_unit_year__academic_year', 'learning_unit_year__learning_container_year',
                            'learning_unit_year__learning_container_year__academic_year') \
            .prefetch_related(entity_container_prefetch) \
            .order_by('learning_unit_year__academic_year__year', 'learning_unit_year__acronym')

        for learning_unit_proposal in proposal:
            append_latest_entities(learning_unit_proposal.learning_unit_year, None)

        return proposal


class ProposalStateModelForm(forms.ModelForm):
    class Meta:
        model = ProposalLearningUnit
        fields = ['state']
