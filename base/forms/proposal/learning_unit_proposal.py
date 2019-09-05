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
from django import forms
from django.utils.translation import ugettext_lazy as _

from base import models as mdl
from base.business.learning_unit_year_with_context import append_latest_entities
from base.forms.learning_unit.search_form import LearningUnitSearchForm
from base.models.entity import Entity
from base.models.enums.proposal_state import ProposalState, LimitedProposalState
from base.models.enums.proposal_type import ProposalType
from base.models.proposal_learning_unit import ProposalLearningUnit


def _get_sorted_choices(tuple_of_choices):
    return LearningUnitSearchForm.ALL_CHOICES + tuple(sorted(tuple_of_choices, key=lambda item: item[1]))


class LearningUnitProposalForm(LearningUnitSearchForm):

    entity_folder_id = forms.ChoiceField(
        label=_('Folder entity'),
        required=False
    )

    folder_id = forms.IntegerField(
        min_value=0,
        required=False,
        label=_('Folder num.'),
        widget=forms.TextInput()
    )

    proposal_type = forms.ChoiceField(
        label=_('Proposal type'),
        choices=_get_sorted_choices(ProposalType.choices()),
        required=False
    )

    proposal_state = forms.ChoiceField(
        label=_('Proposal status'),
        choices=_get_sorted_choices(ProposalState.choices()),
        required=False
    )

    def __init__(self, data, person, *args, **kwargs):
        super().__init__(data, *args, **kwargs)
        self._get_entity_folder_id_linked_ordered_by_acronym(person)

    def _get_entity_folder_id_linked_ordered_by_acronym(self, person):
        entities = Entity.objects.filter(proposallearningunit__isnull=False).distinct()
        entities_sorted_by_acronym = sorted(list(entities.filter(id__in=person.linked_entities)),
                                            key=lambda t: t.most_recent_acronym)
        self.fields['entity_folder_id'].choices = [LearningUnitSearchForm.ALL_LABEL] + \
                                                  [(ent.pk, ent.most_recent_acronym)
                                                   for ent in entities_sorted_by_acronym]

    def get_proposal_learning_units(self):
        learning_units = self.get_queryset().filter(proposallearningunit__isnull=False)

        learning_units = mdl.proposal_learning_unit.filter_proposal_fields(learning_units, **self.cleaned_data)

        for learning_unit in learning_units:
            append_latest_entities(learning_unit, False)

        return learning_units


class ProposalStateModelForm(forms.ModelForm):
    class Meta:
        model = ProposalLearningUnit
        fields = ['state']

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        if kwargs.pop('is_faculty_manager', False):
            self.fields['state'].choices = LimitedProposalState.choices()
