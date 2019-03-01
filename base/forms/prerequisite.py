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

from django import forms
from django.utils.translation import gettext_lazy as _

from base.models import learning_unit
from base.models import prerequisite_item
from base.models.enums.prerequisite_operator import OR, AND
from base.models.prerequisite import Prerequisite, prerequisite_syntax_validator, MULTIPLE_PREREQUISITES_REGEX_OR, \
    MULTIPLE_PREREQUISITES_REGEX_AND


class LearningUnitPrerequisiteForm(forms.ModelForm):
    main_operator = None

    prerequisite_string = forms.CharField(
        label=_("Prerequisite"),
        validators=[prerequisite_syntax_validator],
        required=False,
        help_text=_(
            "<b>Syntax rules</b>:<ul><li>No double parentheses.</li><li>Valid operators are OU or ET.</li><li>The "
            "operator must be the same inside all parentheses (groups).</li><li>The operator that linked groups must "
            "be different than the one that linked LU inside groups (parentheses).</li><li>The LU code cannot include "
            "spaces (ex: LDROI1001 and not LDROI&nbsp;1001).</li></ul></p><p><b>Examples</b>:<ul><li>A OU B OU C: "
            "valid</li><li>A ET B ET C : valid</li><li>A ET (B OU C) ET (D OU E): valid</li><li>A ET (B OU C) OU (D OU "
            "E): not valid</li><li>A ET (B ET C) ET (D ET E): not valid</li><li>A ET (B OU C) ET (D ET E): not valid"
            "</li></ul>"
        ),
    )

    class Meta:
        model = Prerequisite
        fields = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['prerequisite_string'].initial = self.instance.prerequisite_string

    def clean_prerequisite_string(self):
        prerequisite_string = self.cleaned_data['prerequisite_string']
        self.main_operator = _detect_main_operator_in_string(prerequisite_string)

        return self.get_grouped_items_from_string(
            prerequisite_string=prerequisite_string,
            main_operator=self.main_operator
        ) if prerequisite_string else []

    def save(self, commit=True):
        grouped_items = self.cleaned_data['prerequisite_string']

        self.instance.main_operator = self.main_operator or AND
        self.instance.save()

        _create_prerequisite_items(
            grouped_items=grouped_items,
            prerequisite=self.instance
        )

    def get_grouped_items_from_string(self, prerequisite_string, main_operator):
        main_operator_splitter = ' ET ' if main_operator == AND else ' OU '
        secondary_operator_splitter = ' OU ' if main_operator == AND else ' ET '

        groups = prerequisite_string.split(main_operator_splitter)

        return [
            self.split_group_to_learning_units(group, secondary_operator_splitter)
            for group in groups
        ]

    def split_group_to_learning_units(self, group, operator):
        group = _remove_parenthesis(group)
        group = group.split(operator)
        group_of_learning_units = []

        for item in group:
            lu = learning_unit.get_by_acronym_with_highest_academic_year(acronym=item)
            if lu and lu == self.instance.learning_unit_year.learning_unit:
                self.add_error(
                    'prerequisite_string',
                    _("A learning unit cannot be prerequisite to itself : %(acronym)s") % {'acronym': item}
                )
            elif lu:
                # TODO :: Check that lu has a luy which is present in the education_group_year's tree
                group_of_learning_units.append(lu)
            else:
                self.add_error(
                    'prerequisite_string',
                    _("No match has been found for this learning unit :  %(acronym)s") % {'acronym': item}
                )
        return group_of_learning_units


def _create_prerequisite_items(grouped_items, prerequisite):
    for group_number, group in enumerate(grouped_items, 1):
        for position, learning_unit in enumerate(group, 1):
            prerequisite_item.PrerequisiteItem.objects.create(
                prerequisite=prerequisite,
                learning_unit=learning_unit,
                group_number=group_number,
                position=position,
            )


def _remove_parenthesis(string):
    return re.sub('[\(\)]', "", string)


def _detect_main_operator_in_string(prerequisite_string):
    if re.match(MULTIPLE_PREREQUISITES_REGEX_OR, prerequisite_string):
        return OR
    elif re.match(MULTIPLE_PREREQUISITES_REGEX_AND, prerequisite_string):
        return AND
    else:
        return None
