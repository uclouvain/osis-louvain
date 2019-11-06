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
from django_filters import fields as django_filter_fields


class BaseSearchForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            # In a search form, the fields are never required
            field.required = False

    # Should be implemented
    def search(self):
        pass


def get_research_criteria(search_form):
    # TODO : find what is it and what is it use
    tuples_label_value = []
    for field_name, field in search_form.fields.items():
        if not search_form.cleaned_data[field_name]:
            continue
        tuple_to_append = (str(field.label), search_form.cleaned_data[field_name])
        if type(field) == forms.ChoiceField or type(field) == django_filter_fields.ChoiceField:
            dict_choices = {str(key): value for key, value in field.choices}
            label_choice = dict_choices[search_form.cleaned_data[field_name]]
            tuple_to_append = (str(field.label), label_choice)
        tuples_label_value.append(tuple_to_append)
    return tuples_label_value
