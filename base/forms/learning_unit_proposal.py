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
from django.utils.translation import ugettext_lazy as _

from base.business.learning_units.edition import update_or_create_entity_container_year_with_components
from base.business.learning_units.proposal import edition, creation
from base.forms.learning_unit_create import EntitiesVersionChoiceField, LearningUnitYearForm
from base.models import entity_container_year
from base.models.entity_version import find_main_entities_version
from base.models.enums import learning_container_year_types
from base.models.enums.entity_container_year_link_type import ENTITY_TYPE_LIST
from base.models.enums import proposal_state, proposal_type
from base.models import proposal_folder


class LearningUnitProposalModificationForm(LearningUnitYearForm):
    folder_entity = EntitiesVersionChoiceField(queryset=find_main_entities_version())
    folder_id = forms.IntegerField(min_value=0)
    state = forms.ChoiceField(choices=proposal_state.CHOICES)
    type = forms.ChoiceField(choices=proposal_type.CHOICES, required=False, disabled=True)

    def __init__(self, *args, **kwargs):
        self.proposal = kwargs.pop('instance', None)
        super(LearningUnitProposalModificationForm, self).__init__(*args, **kwargs)
        self.fields["academic_year"].disabled = True
        self.fields["academic_year"].required = False
        self.fields["subtype"].required = False
        # When we submit a proposal, we can select all requirement entity available
        self.fields["requirement_entity"].queryset = find_main_entities_version()

    def clean(self):
        cleaned_data = super().clean()

        if cleaned_data.get("internship_subtype") and cleaned_data.get("internship_subtype") != 'None' and \
           cleaned_data["container_type"] != learning_container_year_types.INTERNSHIP:
            self.add_error("internship_subtype", _("learning_unit_type_is_not_internship"))

        return cleaned_data

    def save(self, learning_unit_year, a_person, type_proposal, state_proposal):
        if not self.is_valid():
            raise ValueError("Form is invalid.")

        initial_data = _copy_learning_unit_data(learning_unit_year)
        learning_container_year = learning_unit_year.learning_container_year

        _update_model_object(learning_unit_year.learning_unit, self.cleaned_data, ["periodicity"])
        _update_model_object(learning_unit_year, self.cleaned_data, ["acronym", "status", "quadrimester",
                                                                     "internship_subtype", "credits"])
        learning_container_year.common_title = self.cleaned_data['common_title']
        learning_container_year.common_title_english = self.cleaned_data.get('common_title_english')
        _update_model_object(learning_container_year, self.cleaned_data, ["acronym", "title", "language", "campus",
                                                                          "container_type"])

        for entity_type in ENTITY_TYPE_LIST:
            _update_or_delete_entity_container(self.cleaned_data[entity_type.lower()], learning_container_year,
                                               entity_type)

        folder, created = proposal_folder.ProposalFolder.objects.get_or_create(
            entity=self.cleaned_data['folder_entity'].entity,
            folder_id=self.cleaned_data['folder_id'])

        data = {'person': a_person, 'learning_unit_year': learning_unit_year,
                'state_proposal': state_proposal, 'type_proposal': type_proposal}
        if self.proposal:
            edition.update_learning_unit_proposal(data, self.proposal, folder)
        else:
            data.update({'initial_data': initial_data})
            creation.create_learning_unit_proposal(data, folder)


def _copy_learning_unit_data(learning_unit_year):
    learning_container_year = learning_unit_year.learning_container_year
    entities_by_type = entity_container_year.find_entities_grouped_by_linktype(learning_container_year)

    learning_container_year_values = _get_attributes_values(learning_container_year,
                                                            ["id", "acronym", "common_title", "common_title_english",
                                                             "container_type",
                                                             "campus__id", "language__id", "in_charge"])
    learning_unit_values = _get_attributes_values(learning_unit_year.learning_unit, ["id", "periodicity"])
    learning_unit_year_values = _get_attributes_values(learning_unit_year, ["id", "acronym", "specific_title",
                                                                            "specific_title_english",
                                                                            "internship_subtype", "quadrimester",
                                                                            "status"])
    learning_unit_year_values["credits"] = float(learning_unit_year.credits) if learning_unit_year.credits else None
    return get_initial_data(entities_by_type, learning_container_year_values, learning_unit_values,
                            learning_unit_year_values)


def _update_model_object(obj, data_values, fields_to_update):
    obj_new_values = _create_sub_dictionary(data_values, fields_to_update)
    _set_attributes_from_dict(obj, obj_new_values)
    obj.save()


def _update_or_delete_entity_container(entity_version, learning_container_year, type_entity):
    if not entity_version:
        _delete_entity(learning_container_year, type_entity)
    else:
        update_or_create_entity_container_year_with_components(entity_version.entity, learning_container_year,
                                                               type_entity)


def _delete_entity(learning_container_year, type_entity):
    an_entity_container_year = entity_container_year.\
        find_by_learning_container_year_and_linktype(learning_container_year, type_entity)
    if an_entity_container_year:
        an_entity_container_year.delete()


def _set_attributes_from_dict(obj, attributes_values):
    for key, value in attributes_values.items():
        setattr(obj, key, value)


def _create_sub_dictionary(original_dict, list_keys):
    return {key: value for key, value in original_dict.items() if key in list_keys}


def _get_attributes_values(obj, attributes_name):
    attributes_values = {}
    for attribute_name in attributes_name:
        attributes_hierarchy = attribute_name.split("__")
        value = getattr(obj, attributes_hierarchy[0], None)
        if len(attributes_hierarchy) > 1:
            value = getattr(value, attributes_hierarchy[1], None)
        attributes_values[attributes_hierarchy[0]] = value
    return attributes_values


def get_initial_data(entities_by_type, learning_container_year_values, learning_unit_values, learning_unit_year_values):
    initial_data = {
        "learning_container_year": learning_container_year_values,
        "learning_unit_year": learning_unit_year_values,
        "learning_unit": learning_unit_values,
        "entities": get_entities(entities_by_type)
    }
    return initial_data


def get_entities(entities_by_type):
    return {entity_type: get_entity_by_type(entity_type, entities_by_type) for entity_type in ENTITY_TYPE_LIST}


def get_entity_by_type(entity_type, entities_by_type):
    if entities_by_type.get(entity_type):
        return entities_by_type[entity_type].id
    else:
        return None
