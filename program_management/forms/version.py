##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2020 Université catholique de Louvain (http://www.uclouvain.be)
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
from django.forms import TextInput
from django.utils.translation import gettext_lazy as _

from base.forms.utils.choice_field import BLANK_CHOICE
from base.models.academic_year import current_academic_year
from education_group.ddd.business_types import *
from education_group.templatetags.academic_year_display import display_as_academic_year
from program_management.ddd.command import GetEndPostponementYearCommand
from program_management.ddd.domain.node import NodeIdentity
from program_management.ddd.service.read import get_end_postponement_year_service


class SpecificVersionForm(forms.Form):
    version_name = forms.CharField(
        max_length=15,
        required=True,
        label=_('Acronym of version'),
        widget=TextInput(
            attrs={'onchange': 'validate_version_name()', 'style': "text-transform: uppercase;"}
        ),
    )
    title = forms.CharField(
        max_length=100,
        required=False,
        label=_('Full title of the french version'),
    )
    title_english = forms.CharField(
        max_length=100,
        required=False,
        label=_('Full title of the english version'),
    )
    end_year = forms.ChoiceField(
        required=False,
        label=_('This version exists until'),
    )

    def __init__(self, training_identity: 'TrainingIdentity', node_identity: 'NodeIdentity', *args, **kwargs):
        self.training_identity = training_identity
        self.node_identity = node_identity
        super().__init__(*args, **kwargs)

        self.__init_academic_year_choices()

    def __init_academic_year_choices(self):
        # TODO :: unit tests on this service (or on the domain service)
        max_year = get_end_postponement_year_service.calculate_program_tree_end_postponement(
            GetEndPostponementYearCommand(code=self.node_identity.code, year=self.node_identity.year)
        )
        choices_years = [(x, display_as_academic_year(x)) for x in range(self.training_identity.year, max_year + 1)]

        if max_year == current_academic_year().year+6:
            self.fields["end_year"].choices = BLANK_CHOICE + choices_years
        else:
            self.fields["end_year"].choices = choices_years
            self.fields["end_year"].initial = choices_years[-1]

    def clean_end_year(self):
        end_year = self.cleaned_data["end_year"]
        return int(end_year) if end_year else None

    def clean_version_name(self):
        return self.cleaned_data['version_name'].upper()
