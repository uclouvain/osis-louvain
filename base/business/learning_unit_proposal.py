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
from base.business.learning_units.edition import update_or_create_entity_container_year_with_components
from base.business.learning_units.simple import deletion as business_deletion
from base.models import entity_container_year, campus, entity
from base.models.enums import entity_container_year_link_type
from base.models.enums.proposal_type import ProposalType
from base.utils import send_mail as send_mail_util
from reference.models import language
from django.utils.translation import ugettext_lazy as _
from base import models as mdl_base
from django.apps import apps
from django.contrib.messages import ERROR, SUCCESS

APP_BASE_LABEL = 'base'
END_FOREIGN_KEY_NAME = "_id"
NO_PREVIOUS_VALUE = '-'
# TODO : VALUES_WHICH_NEED_TRANSLATION ?
VALUES_WHICH_NEED_TRANSLATION = ["periodicity", "container_type", "internship_subtype"]
LABEL_ACTIVE = _('active')
LABEL_INACTIVE = _('inactive')


def compute_proposal_type(initial_data, current_data):
    data_changed = _compute_data_changed(initial_data, current_data)

    if _is_transformation(initial_data, current_data):
        if _is_modification(data_changed):
            proposal_type = ProposalType.TRANSFORMATION_AND_MODIFICATION.name
        else:
            proposal_type = ProposalType.TRANSFORMATION.name
    else:
        proposal_type = ProposalType.MODIFICATION.name

    return proposal_type


def _compute_data_changed(initial_data, current_data):
    data_changed = {}
    for key, value in current_data.items():
        initial_value = initial_data.get(key)
        if key == 'status':
            value = value == 'on'
        if _is_initial_not_equal_current(initial_value, value):
            data_changed[key] = value
    return data_changed


def _is_initial_not_equal_current(initial_value, value):
    return initial_value and value and str(value) != str(initial_value)


def _is_transformation(initial_data, current_data):
    if 'acronym' not in initial_data:
        return False
    return (current_data.get("first_letter", "") + current_data["acronym"] !=
            initial_data.get("first_letter", "") + initial_data["acronym"])


def _is_modification(data_changed):
    if data_changed.get('acronym'):
        del data_changed['acronym']
    if data_changed.get('first_letter'):
        del data_changed['first_letter']
    return bool(data_changed)


def reinitialize_data_before_proposal(learning_unit_proposal):
    learning_unit_year = learning_unit_proposal.learning_unit_year
    initial_data = learning_unit_proposal.initial_data
    _reinitialize_model_before_proposal(learning_unit_year, initial_data["learning_unit_year"])
    _reinitialize_model_before_proposal(learning_unit_year.learning_unit, initial_data["learning_unit"])
    _reinitialize_model_before_proposal(learning_unit_year.learning_container_year,
                                        initial_data["learning_container_year"])
    _reinitialize_entities_before_proposal(learning_unit_year.learning_container_year,
                                           initial_data["entities"])


def _reinitialize_model_before_proposal(obj_model, attribute_initial_values):
    for attribute_name, attribute_value in attribute_initial_values.items():
        if attribute_name != "id":
            cleaned_initial_value = _clean_attribute_initial_value(attribute_name, attribute_value)
            setattr(obj_model, attribute_name, cleaned_initial_value)
    obj_model.save()


def _clean_attribute_initial_value(attribute_name, attribute_value):
    clean_attribute_value = attribute_value
    if attribute_name == "campus":
        clean_attribute_value = campus.find_by_id(attribute_value)
    elif attribute_name == "language":
        clean_attribute_value = language.find_by_id(attribute_value)
    return clean_attribute_value


def _reinitialize_entities_before_proposal(learning_container_year, initial_entities_by_type):
    for type_entity, id_entity in initial_entities_by_type.items():
        initial_entity = entity.get_by_internal_id(id_entity)
        if initial_entity:
            update_or_create_entity_container_year_with_components(initial_entity, learning_container_year, type_entity)
        else:
            current_entity_container_year = entity_container_year.find_by_learning_container_year_and_linktype(
                learning_container_year, type_entity)
            if current_entity_container_year is not None:
                current_entity_container_year.delete()


def delete_learning_unit_proposal(learning_unit_proposal):
    prop_type = learning_unit_proposal.type
    lu = learning_unit_proposal.learning_unit_year.learning_unit
    learning_unit_proposal.delete()
    if prop_type == ProposalType.CREATION.name:
        lu.delete()


def get_difference_of_proposal(learning_unit_yr_proposal):
    differences = {}
    if learning_unit_yr_proposal and learning_unit_yr_proposal.initial_data.get('learning_container_year'):
        differences.update(_get_differences_in_learning_unit_data(learning_unit_yr_proposal))
        learning_container_yr = mdl_base.learning_container_year \
            .find_by_id(learning_unit_yr_proposal.initial_data.get('learning_container_year').get('id'))
        if learning_container_yr:
            differences.update(_get_difference_of_entity_proposal(learning_container_yr, learning_unit_yr_proposal))

    return differences


def _get_difference_of_entity_proposal(learning_container_yr, learning_unit_yr_proposal):
    differences = {}
    for entity_type, initial_entity_id in learning_unit_yr_proposal.initial_data.get('entities').items():
        entity_cont_yr = mdl_base.entity_container_year \
            .find_by_learning_container_year_and_linktype(learning_container_yr, entity_type)
        if entity_cont_yr:
            differences.update(_get_entity_old_value(entity_cont_yr, initial_entity_id, entity_type))
        elif initial_entity_id:
            differences.update(_get_entity_previous_value(initial_entity_id, entity_type))
    return differences


def _get_entity_old_value(entity_cont_yr, initial_entity_id, entity_type):
    differences = {}
    if _has_changed_entity(entity_cont_yr, initial_entity_id):
        differences.update(_get_entity_previous_value(initial_entity_id, entity_type))
    elif not initial_entity_id and entity_type in (entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_1,
                                                   entity_container_year_link_type.ADDITIONAL_REQUIREMENT_ENTITY_2):
            differences.update({entity_type: NO_PREVIOUS_VALUE})
    return differences


def _has_changed_entity(entity_cont_yr, entity_id):
    return entity_id and entity_cont_yr.entity.id != entity_id


def _get_differences_in_learning_unit_data(proposal):
    learning_unit_yr_initial_data = _get_data_dict('learning_unit_year', proposal.initial_data)
    learning_container_yr_initial_data = _get_data_dict('learning_container_year', proposal.initial_data)
    initial_learning_container_yr_id = _get_data_dict('id', learning_container_yr_initial_data)
    learning_unit_initial_data = _get_data_dict('learning_unit', proposal.initial_data)

    differences = {}
    differences.update(_compare_model_with_initial_value(proposal.learning_unit_year.id,
                                                         learning_unit_yr_initial_data,
                                                         apps.get_model(app_label=APP_BASE_LABEL,
                                                                        model_name="LearningUnitYear")))
    if initial_learning_container_yr_id:
        differences.update(_compare_model_with_initial_value(initial_learning_container_yr_id,
                                                             learning_container_yr_initial_data,
                                                             apps.get_model(app_label=APP_BASE_LABEL,
                                                                            model_name="LearningContainerYear")))
    if learning_unit_initial_data:
        differences.update(_compare_model_with_initial_value(learning_unit_initial_data.get('id'),
                                                             learning_unit_initial_data,
                                                             apps.get_model(app_label=APP_BASE_LABEL,
                                                                            model_name="LearningUnit")))
    return differences


def _compare_model_with_initial_value(an_id, model_initial_data, mymodel):
    differences = {}
    qs = mymodel.objects.filter(pk=an_id).values()
    if len(qs) > 0:
        differences.update(_check_differences(model_initial_data, _get_rid_of_blank_value(qs[0])))
    return differences


def _replace_key_of_foreign_key(data):
    return {key_name.replace(END_FOREIGN_KEY_NAME, ''): data[key_name] for key_name in data.keys()}


def _check_differences(initial_data, current_data):
    if initial_data:
        return _compare_initial_current_data(current_data, initial_data)
    return {}


def _compare_initial_current_data(current_data, initial_data):
    corrected_dict = _replace_key_of_foreign_key(current_data)
    differences = {}
    for attribute, initial_value in initial_data.items():
        if attribute in corrected_dict and initial_data.get(attribute, None) != corrected_dict.get(attribute):
            differences.update(_get_the_old_value(attribute, current_data, initial_data))
    return differences


def _get_the_old_value(key, current_data, initial_data):
    initial_value = initial_data.get(key) or NO_PREVIOUS_VALUE

    if _is_foreign_key(key, current_data):
        return _get_str_representing_old_data_from_foreign_key(key, initial_value)
    else:
        return _get_old_value_when_not_foreign_key(initial_value, key)


def _get_str_representing_old_data_from_foreign_key(key, initial_value):
    if initial_value != NO_PREVIOUS_VALUE:
        return _get_old_value_of_foreign_key(key, initial_value)
    else:
        return {key: NO_PREVIOUS_VALUE}


def _get_old_value_of_foreign_key(key, initial_value):
    differences = {}
    if key == 'campus':
        differences.update({key: str(mdl_base.campus.find_by_id(initial_value))})

    if key == 'language':
        differences.update({key: str(language.find_by_id(initial_value))})
    return differences


def _is_foreign_key(key, current_data):
    return "{}{}".format(key, END_FOREIGN_KEY_NAME) in current_data


def _get_entity_previous_value(entity_id, entity_type):
    if entity_id:
        old_value = entity.find_by_id(entity_id)
        if old_value:
            return {entity_type: old_value.most_recent_acronym}
    return {entity_type: _('entity_not_found')}


def _get_data_dict(key, initial_data):
    if initial_data:
        return initial_data.get(key) if initial_data.get(key) else None
    return None


def _get_status_initial_value(initial_value, key):
    return {key: LABEL_ACTIVE} if initial_value else {key: LABEL_INACTIVE}


def _get_old_value_when_not_foreign_key(initial_value, key):
    if key in VALUES_WHICH_NEED_TRANSLATION and initial_value != NO_PREVIOUS_VALUE:
        return {key: "{}".format(_(initial_value))}
    elif key == 'status':
        return _get_status_initial_value(initial_value, key)
    else:
        return {key: "{}".format(initial_value)}


def _get_rid_of_blank_value(data):
    clean_data = data.copy()
    for key, value in clean_data.items():
        if value == '':
            clean_data[key] = None
    return clean_data


def cancel_proposal(learning_unit_proposal, author, send_mail=True):
    acronym = learning_unit_proposal.learning_unit_year.acronym
    error_messages = []
    success_messages = []
    if learning_unit_proposal.type == ProposalType.CREATION.name:
        learning_unit_year = learning_unit_proposal.learning_unit_year
        error_messages.extend(business_deletion.check_can_delete_ignoring_proposal_validation(learning_unit_year))
        if not error_messages:
            success_messages.extend(business_deletion.delete_from_given_learning_unit_year(learning_unit_year))
    else:
        reinitialize_data_before_proposal(learning_unit_proposal)
    delete_learning_unit_proposal(learning_unit_proposal)
    success_messages.append(_("success_cancel_proposal").format(acronym))
    if send_mail:
        send_mail_util.send_mail_after_the_learning_unit_proposal_cancellation([author], [learning_unit_proposal])
    return {
        SUCCESS: success_messages,
        ERROR: error_messages
    }


def cancel_proposals(proposals_to_cancel, author):
    success_messages = []
    error_messages = []
    for proposal in proposals_to_cancel:
        messages_by_level = cancel_proposal(proposal, author, send_mail=False)
        success_messages.extend(messages_by_level[SUCCESS])
        error_messages.extend(messages_by_level[ERROR])
    send_mail_util.send_mail_after_the_learning_unit_proposal_cancellation([author], [proposals_to_cancel])
    return {
        SUCCESS: success_messages,
        ERROR: error_messages
    }
