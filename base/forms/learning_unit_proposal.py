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
from django import forms
from django.utils.translation import ugettext_lazy as _

from base.forms.learning_units import CreateLearningUnitYearForm, EntitiesVersionChoiceField
from base.models.entity_version import find_main_entities_version
from base.models import proposal_folder, proposal_learning_unit, entity_container_year
from base.models.enums import learning_container_year_types
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY, ALLOCATION_ENTITY, \
    ADDITIONAL_REQUIREMENT_ENTITY_1, ADDITIONAL_REQUIREMENT_ENTITY_2


def add_none_choice(choices):
    return ((None, "-----"),) + choices


class LearningUnitProposalModificationForm(CreateLearningUnitYearForm):
    folder_entity = EntitiesVersionChoiceField(queryset=find_main_entities_version())
    folder_id = forms.IntegerField(min_value=0)

    def __init__(self, *args, **kwargs):
        super(LearningUnitProposalModificationForm, self).__init__(None, *args, **kwargs)
        self.fields["academic_year"].disabled = True
        self.fields["academic_year"].required = False
        self.fields["subtype"].required = False
        # When we submit a proposal, we can select all requirement entity available
        self.fields["requirement_entity"].queryset = find_main_entities_version()

    def clean(self):
        cleaned_data = super(CreateLearningUnitYearForm, self).clean()

        if cleaned_data.get("internship_subtype") and cleaned_data.get("internship_subtype") != 'None' and \
           cleaned_data["container_type"] != learning_container_year_types.INTERNSHIP:
            self.add_error("internship_subtype", _("learning_unit_type_is_not_internship"))

    def save(self, learning_unit_year, a_person, type_proposal, state_proposal):
        if not self.is_valid():
            raise ValueError("Form is invalid.")

        initial_data = _copy_learning_unit_data(learning_unit_year)

        learning_container_year = learning_unit_year.learning_container_year

        _update_model_object(learning_unit_year.learning_unit, self.cleaned_data, ["periodicity"])
        _update_model_object(learning_unit_year, self.cleaned_data, ["acronym", "title", "title_english", "status",
                                                                     "quadrimester", "internship_subtype", "credits"])
        _update_model_object(learning_container_year, self.cleaned_data, ["acronym", "title", "language",
                                                                          "title_english", "campus", "container_type"])

        _update_entity(self.cleaned_data["requirement_entity"], learning_container_year, REQUIREMENT_ENTITY)
        _update_entity(self.cleaned_data["allocation_entity"], learning_container_year, ALLOCATION_ENTITY)
        _update_entity(self.cleaned_data["additional_entity_1"], learning_container_year,
                       ADDITIONAL_REQUIREMENT_ENTITY_1)
        _update_entity(self.cleaned_data["additional_entity_2"], learning_container_year,
                       ADDITIONAL_REQUIREMENT_ENTITY_2)

        folder_entity = self.cleaned_data['folder_entity'].entity
        folder_id = self.cleaned_data['folder_id']

        _create_learning_unit_proposal(a_person, folder_entity, folder_id, initial_data, learning_unit_year,
                                       state_proposal, type_proposal)


def _copy_learning_unit_data(learning_unit_year):
    learning_container_year = learning_unit_year.learning_container_year
    entities_by_type = entity_container_year.find_entities_grouped_by_linktype(learning_container_year)

    learning_container_year_values = _get_attributes_values(learning_container_year,
                                                            ["id", "acronym", "title", "title_english", "container_type",
                                                            "campus__id", "language__id", "in_charge"])
    learning_unit_values = _get_attributes_values(learning_unit_year.learning_unit, ["id", "periodicity"])
    learning_unit_year_values = _get_attributes_values(learning_unit_year, ["id", "acronym", "title", "title_english",
                                                                           "internship_subtype", "quadrimester"])
    learning_unit_year_values["credits"] = float(learning_unit_year.credits) if learning_unit_year.credits else None
    initial_data = {
        "learning_container_year": learning_container_year_values,
        "learning_unit_year": learning_unit_year_values,
        "learning_unit": learning_unit_values,
        "entities": {
            REQUIREMENT_ENTITY: entities_by_type[REQUIREMENT_ENTITY].id
            if entities_by_type.get(REQUIREMENT_ENTITY) else None,
            ALLOCATION_ENTITY: entities_by_type[ALLOCATION_ENTITY].id
            if entities_by_type.get(ALLOCATION_ENTITY) else None,
            ADDITIONAL_REQUIREMENT_ENTITY_1: entities_by_type[ADDITIONAL_REQUIREMENT_ENTITY_1].id
            if entities_by_type.get(ADDITIONAL_REQUIREMENT_ENTITY_1) else None,
            ADDITIONAL_REQUIREMENT_ENTITY_2: entities_by_type[ADDITIONAL_REQUIREMENT_ENTITY_2].id
            if entities_by_type.get(ADDITIONAL_REQUIREMENT_ENTITY_2) else None
        }
    }
    return initial_data


def _update_model_object(obj, data_values, fields_to_update):
    obj_new_values = _create_sub_dictionary(data_values, fields_to_update)
    _set_attributes_from_dict(obj, obj_new_values)
    obj.save()


def _update_entity(entity_version, learning_container_year, type_entity):
    if not entity_version:
        return
    entity_container_year.EntityContainerYear.objects.update_or_create(type=type_entity,
                                                                       learning_container_year=learning_container_year,
                                                                       defaults={"entity": entity_version.entity})


def _create_learning_unit_proposal(a_person, folder_entity, folder_id, initial_data, learning_unit_year,
                                   state_proposal, type_proposal):
    folder, created = proposal_folder.ProposalFolder.objects.get_or_create(entity=folder_entity, folder_id=folder_id)

    proposal_learning_unit.ProposalLearningUnit.objects.create(folder=folder, learning_unit_year=learning_unit_year,
                                                               type=type_proposal, state=state_proposal,
                                                               initial_data=initial_data, author=a_person)


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






