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
import datetime

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import ugettext_lazy as _
from waffle.models import Flag

from base.business.institution import find_summary_course_submission_dates_for_entity_version
from base.business.learning_units.prerequisite import luy_has_or_is_prerequisite
from base.models import proposal_learning_unit, tutor
from base.models.academic_year import MAX_ACADEMIC_YEAR_FACULTY, MAX_ACADEMIC_YEAR_CENTRAL, \
    starting_academic_year
from base.models.entity import Entity
from base.models.entity_version import find_last_entity_version_by_learning_unit_year_id
from base.models.enums import learning_container_year_types, entity_container_year_link_type
from base.models.enums.entity_container_year_link_type import REQUIREMENT_ENTITY
from base.models.enums.proposal_state import ProposalState
from base.models.enums.proposal_type import ProposalType
from base.models.learning_unit_year import LearningUnitYear
from base.models.person import is_person_linked_to_entity_in_charge_of_learning_unit
from osis_common.utils.datetime import get_tzinfo, convert_date_to_datetime
from osis_common.utils.perms import conjunction, disjunction, negation, BasePerm

FACULTY_UPDATABLE_CONTAINER_TYPES = (learning_container_year_types.COURSE,
                                     learning_container_year_types.DISSERTATION,
                                     learning_container_year_types.INTERNSHIP)

PROPOSAL_CONSOLIDATION_ELIGIBLE_STATES = (ProposalState.ACCEPTED.name,
                                          ProposalState.REFUSED.name)

MSG_EXISTING_PROPOSAL_IN_EPC = _("Existing proposal in epc")
MSG_NO_ELIGIBLE_TO_MODIFY_END_DATE = _("You are not eligible to modify the end date of this learning unit. You should "
                                       "be central manager or the learning unit has to be a partim or the learning unit"
                                       " as to be a course/dissertation/internship")
MSG_CANNOT_MODIFY_ON_PREVIOUS_ACADEMIC_YR = _("You can't modify learning unit of a previous year")
MSG_ONLY_IF_YOUR_ARE_LINK_TO_ENTITY = _("You can only modify a learning unit when your are linked to its requirement "
                                        "entity")
MSG_LEARNING_UNIT_IS_OR_HAS_PREREQUISITE = _("You cannot delete a learning unit which is prerequisite or has "
                                             "prerequisite(s)")
MSG_PERSON_NOT_IN_ACCORDANCE_WITH_PROPOSAL_STATE = _("Person not in accordance with proposal state")
MSG_NOT_PROPOSAL_STATE_FACULTY = _("You are faculty manager and the proposal state is not 'Faculty', so you can't edit")
MSG_NOT_ELIGIBLE_TO_CANCEL_PROPOSAL = _("You are not eligible to cancel proposal")
MSG_NOT_ELIGIBLE_TO_EDIT_PROPOSAL = _("You are not eligible to edit proposal")
MSG_CAN_EDIT_PROPOSAL_NO_LINK_TO_ENTITY = _("You are not attached to initial or current requirement entity, so you "
                                            "can't edit proposal")
MSG_NOT_GOOD_RANGE_OF_YEARS = _("Not in range of years which can be edited by you")
MSG_NOT_ELIGIBLE_TO_CONSOLIDATE_PROPOSAL = _("You are not eligible to consolidate proposal")
MSG_NO_RIGHTS_TO_CONSOLIDATE = _("You don't have the rights to consolidate")
MSG_PROPOSAL_NOT_IN_CONSOLIDATION_ELIGIBLE_STATES = _("Proposal not in eligible state for consolidation")
MSG_CAN_DELETE_ACCORDING_TO_TYPE = _("Can delete according to the type of the learning unit")
MSG_NOT_ELIGIBLE_TO_DELETE_LU = _("Not eligible to delete learning units")
MSG_NOT_ELIGIBLE_TO_CREATE_MODIFY_PROPOSAL = _("You are not eligible to create/modify proposal")
MSG_PROPOSAL_IS_ON_AN_OTHER_YEAR = _("You can't modify proposal which is on an other year")
MSG_NOT_ELIGIBLE_FOR_MODIFICATION_BECAUSE_OF_TYPE = _("This learning unit isn't eligible for modification because of "
                                                      "it's type")


def _any_existing_proposal_in_epc(learning_unit_year, _, raise_exception=False):
    result = not learning_unit_year.learning_unit.existing_proposal_in_epc
    can_raise_exception(
        raise_exception,
        result,
        MSG_EXISTING_PROPOSAL_IN_EPC,
    )
    return result


def is_eligible_for_modification(learning_unit_year, person, raise_exception=False):
    result = \
        is_year_editable(learning_unit_year, person, raise_exception) and \
        _any_existing_proposal_in_epc(learning_unit_year, person, raise_exception) and \
        _is_learning_unit_year_in_range_to_be_modified(learning_unit_year, person, raise_exception) and \
        is_person_linked_to_entity_in_charge_of_lu(learning_unit_year, person, raise_exception)
    return result


def is_eligible_for_modification_end_date(learning_unit_year, person, raise_exception=False):
    return \
        is_year_editable(learning_unit_year, person, raise_exception) and \
        not (is_learning_unit_year_in_past(learning_unit_year, person, raise_exception)) and \
        is_eligible_for_modification(learning_unit_year, person, raise_exception) and \
        _is_person_eligible_to_modify_end_date_based_on_container_type(learning_unit_year, person, raise_exception)


def is_eligible_to_create_partim(learning_unit_year, person, raise_exception=False):
    return conjunction(
        _any_existing_proposal_in_epc,
        is_person_linked_to_entity_in_charge_of_lu,
        is_academic_year_in_range_to_create_partim,
        is_learning_unit_year_full
    )(learning_unit_year, person, raise_exception)


def is_eligible_to_create_modification_proposal(learning_unit_year, person, raise_exception=False):
    result = \
        _any_existing_proposal_in_epc(learning_unit_year, person, raise_exception) and \
        not(is_learning_unit_year_in_past(learning_unit_year, person, raise_exception))and \
        not(is_learning_unit_year_a_partim(learning_unit_year, person, raise_exception))and \
        _is_container_type_course_dissertation_or_internship(learning_unit_year, person, raise_exception)and \
        not(is_learning_unit_year_in_proposal(learning_unit_year, person, raise_exception))and \
        is_person_linked_to_entity_in_charge_of_learning_unit(learning_unit_year, person, raise_exception)
    #  TODO detail why button is disabled
    can_raise_exception(
        raise_exception, result,
        MSG_NOT_ELIGIBLE_TO_CREATE_MODIFY_PROPOSAL
    )
    return result


def is_eligible_for_cancel_of_proposal(proposal, person, raise_exception=False):
    result = \
        _is_person_in_accordance_with_proposal_state(proposal, person, raise_exception) and \
        _is_attached_to_initial_or_current_requirement_entity(proposal, person, raise_exception) and \
        _has_person_the_right_to_make_proposal(proposal, person, raise_exception)
    can_raise_exception(
        raise_exception, result,
        MSG_NOT_ELIGIBLE_TO_CANCEL_PROPOSAL
    )
    return result


def is_eligible_to_edit_proposal(proposal, person, raise_exception=False):
    if not proposal:
        return False

    result = \
        _is_attached_to_initial_or_current_requirement_entity(proposal, person, raise_exception) and \
        _is_person_eligible_to_edit_proposal_based_on_state(proposal, person, raise_exception) and \
        _has_person_the_right_edit_proposal(proposal, person)
    can_raise_exception(
        raise_exception, result,
        MSG_NOT_ELIGIBLE_TO_EDIT_PROPOSAL
    )
    return result


def is_eligible_to_consolidate_proposal(proposal, person, raise_exception=False):
    msg = None

    if not _has_person_the_right_to_consolidate(proposal, person):
        msg = MSG_NO_RIGHTS_TO_CONSOLIDATE
    elif not _is_proposal_in_state_to_be_consolidated(proposal, person):
        msg = MSG_PROPOSAL_NOT_IN_CONSOLIDATION_ELIGIBLE_STATES
    elif not _is_attached_to_initial_or_current_requirement_entity(proposal, person, raise_exception):
        msg = MSG_CAN_EDIT_PROPOSAL_NO_LINK_TO_ENTITY

    result = False if msg else True
    can_raise_exception(
        raise_exception,
        result,
        msg
    )
    return result


def can_edit_summary_locked_field(learning_unit_year, person):
    flag = Flag.get('educational_information_block_action')
    return flag.is_active_for_user(person.user) and \
        person.is_faculty_manager() and \
        person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year)


def can_update_learning_achievement(learning_unit_year, person):
    return person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year)


def is_eligible_to_delete_learning_unit_year(learning_unit_year, person, raise_exception=False):
    msg = None
    checked_ok = \
        _any_existing_proposal_in_epc(learning_unit_year, person, raise_exception) and \
        _can_delete_learning_unit_year_according_type(learning_unit_year, person, raise_exception)
    if not checked_ok:
        msg = MSG_NOT_ELIGIBLE_TO_DELETE_LU
    elif not person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year):
        msg = MSG_ONLY_IF_YOUR_ARE_LINK_TO_ENTITY
    elif luy_has_or_is_prerequisite(learning_unit_year):
        msg = MSG_LEARNING_UNIT_IS_OR_HAS_PREREQUISITE

    result = False if msg else True
    can_raise_exception(
        raise_exception,
        result,
        msg
    )

    return result


def _is_person_eligible_to_edit_proposal_based_on_state(proposal, person, raise_exception=False):
    if person.is_central_manager():
        return True
    if proposal.state != ProposalState.FACULTY.name:
        can_raise_exception(
            raise_exception,
            False,
            MSG_NOT_PROPOSAL_STATE_FACULTY
        )
        return False
    if proposal.type == ProposalType.MODIFICATION.name and \
       proposal.learning_unit_year.academic_year.year != starting_academic_year().year + 1:
        can_raise_exception(
            raise_exception,
            False,
            MSG_PROPOSAL_IS_ON_AN_OTHER_YEAR
        )
        return False
    return True


def _is_person_eligible_to_modify_end_date_based_on_container_type(learning_unit_year, person, raise_exception=False):
    result = disjunction(
        _is_person_central_manager,
        _is_learning_unit_year_a_partim,
        negation(_is_container_type_course_dissertation_or_internship2),
    )(learning_unit_year, person, raise_exception)

    can_raise_exception(
        raise_exception,
        result,
        MSG_NO_ELIGIBLE_TO_MODIFY_END_DATE,
    )
    return result


def is_eligible_to_manage_charge_repartition(learning_unit_year, person):
    return person.user.has_perm("base.can_manage_charge_repartition") and \
        learning_unit_year.is_partim() and \
        person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year)


def is_eligible_to_manage_attributions(learning_unit_year, person):
    container_types = (learning_container_year_types.OTHER_COLLECTIVE, learning_container_year_types.OTHER_INDIVIDUAL,
                       learning_container_year_types.MASTER_THESIS)
    return person.user.has_perm("base.can_manage_attribution") and \
        learning_unit_year.learning_container_year.container_type in container_types and \
        person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year)


def _is_person_central_manager(_, person, raise_exception):
    return person.is_central_manager()


def _is_learning_unit_year_a_partim(learning_unit_year, _, raise_exception=False):
    return learning_unit_year.is_partim()


def _is_person_in_accordance_with_proposal_state(proposal, person, raise_exception=False):
    result = (person.is_central_manager()) or proposal.state == ProposalState.FACULTY.name
    can_raise_exception(
        raise_exception, result,
        MSG_PERSON_NOT_IN_ACCORDANCE_WITH_PROPOSAL_STATE
    )
    return result


def _has_person_the_right_to_make_proposal(_, person, raise_exception=False):
    result = person.user.has_perm('base.can_propose_learningunit')
    can_raise_exception(
        raise_exception, result,
        "_has_person_the_right_to_make_proposal")
    return result


def _has_person_the_right_edit_proposal(_, person):
    return person.user.has_perm('base.can_edit_learning_unit_proposal')


def _has_person_the_right_to_consolidate(_, person):
    return person.user.has_perm('base.can_consolidate_learningunit_proposal')


def is_learning_unit_year_full(learning_unit_year, _, raise_exception=False):
    return learning_unit_year.is_full()


def is_learning_unit_year_in_past(learning_unit_year, _, raise_exception=False):
    result = learning_unit_year.is_past()
    can_raise_exception(
        raise_exception,
        not result,
        MSG_CANNOT_MODIFY_ON_PREVIOUS_ACADEMIC_YR
    )
    return result


def is_learning_unit_year_a_partim(learning_unit_year, _, raise_exception=False):
    return learning_unit_year.is_partim()


def is_learning_unit_year_in_proposal(learning_unit_year, _, raise_exception=False):
    return proposal_learning_unit.is_learning_unit_in_proposal(learning_unit_year.learning_unit)


def is_academic_year_in_range_to_create_partim(learning_unit_year, person, raise_exception=False):
    current_acy = starting_academic_year()
    luy_acy = learning_unit_year.academic_year
    max_range = MAX_ACADEMIC_YEAR_FACULTY if person.is_faculty_manager() else MAX_ACADEMIC_YEAR_CENTRAL

    return current_acy.year <= luy_acy.year <= current_acy.year + max_range


def _is_learning_unit_year_in_range_to_be_modified(learning_unit_year, person, raise_exception):
    result = person.is_central_manager() or learning_unit_year.can_update_by_faculty_manager()
    can_raise_exception(
        raise_exception,
        result,
        MSG_NOT_GOOD_RANGE_OF_YEARS,
        )
    return result


def _is_proposal_in_state_to_be_consolidated(proposal, _):
    return proposal.state in PROPOSAL_CONSOLIDATION_ELIGIBLE_STATES


def _can_delete_learning_unit_year_according_type(learning_unit_year, person, raise_exception=False):
    if not person.is_central_manager() and person.is_faculty_manager():
        container_type = learning_unit_year.learning_container_year.container_type
        result = not (
            container_type == learning_container_year_types.COURSE and learning_unit_year.is_full()
        ) and container_type not in [learning_container_year_types.DISSERTATION,
                                     learning_container_year_types.INTERNSHIP]
    else:
        result = True

    can_raise_exception(
        raise_exception,
        result,
        MSG_CAN_DELETE_ACCORDING_TO_TYPE
    )
    return result


def _is_attached_to_initial_or_current_requirement_entity(proposal, person, raise_exception=False):
    result = \
        _is_attached_to_initial_entity(proposal, person) or \
        person.is_linked_to_entity_in_charge_of_learning_unit_year(proposal.learning_unit_year)

    can_raise_exception(
        raise_exception,
        result,
        MSG_CAN_EDIT_PROPOSAL_NO_LINK_TO_ENTITY
    )
    return result


def _is_attached_to_initial_entity(learning_unit_proposal, a_person):
    if not learning_unit_proposal.initial_data.get("entities") or \
            not learning_unit_proposal.initial_data["entities"].get(REQUIREMENT_ENTITY):
        return False
    initial_entity_requirement_id = learning_unit_proposal.initial_data["entities"][REQUIREMENT_ENTITY]
    return a_person.is_attached_entities(Entity.objects.filter(pk=initial_entity_requirement_id))


def _is_container_type_course_dissertation_or_internship(learning_unit_year, _, raise_exception):
    result = \
        learning_unit_year.learning_container_year and \
        learning_unit_year.learning_container_year.container_type in FACULTY_UPDATABLE_CONTAINER_TYPES

    can_raise_exception(
        raise_exception,
        result,
        MSG_NOT_ELIGIBLE_FOR_MODIFICATION_BECAUSE_OF_TYPE
    )
    return result


def learning_unit_year_permissions(learning_unit_year, person):
    return {
        'can_propose': is_eligible_to_create_modification_proposal(learning_unit_year, person),
        'can_edit_date': is_eligible_for_modification_end_date(learning_unit_year, person),
        'can_edit': is_eligible_for_modification(learning_unit_year, person),
        'can_delete': is_eligible_to_delete_learning_unit_year(learning_unit_year, person),
    }


def learning_unit_proposal_permissions(proposal, person, current_learning_unit_year):
    permissions = {'can_cancel_proposal': False, 'can_edit_learning_unit_proposal': False,
                   'can_consolidate_proposal': False}
    if not proposal or proposal.learning_unit_year != current_learning_unit_year:
        return permissions
    permissions['can_cancel_proposal'] = is_eligible_for_cancel_of_proposal(proposal, person)
    permissions['can_edit_learning_unit_proposal'] = is_eligible_to_edit_proposal(proposal, person)
    permissions['can_consolidate_proposal'] = is_eligible_to_consolidate_proposal(proposal, person)
    return permissions


def is_eligible_to_update_learning_unit_pedagogy(learning_unit_year, person):
    """
    Permission to edit learning unit pedagogy needs many conditions:
        - The person must have the permission can_edit_learning_pedagogy
        - The person must be link to requirement entity
        - The person can be a faculty or a central manager
        - The person can be a tutor:
            - The learning unit must have its flag summary_locked to false
            - The person must have an attribution for the learning unit year
            - The attribution must have its flag summary responsible to true.

    :param learning_unit_year: LearningUnitYear
    :param person: Person
    :return: bool
    """
    if not person.user.has_perm('base.can_edit_learningunit_pedagogy'):
        return False

    # Case faculty/central: We need to check if user is linked to entity
    if person.is_faculty_manager() or person.is_central_manager():
        return person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year)

    # Case Tutor: We need to check if today is between submission date
    if tutor.is_tutor(person.user):
        return can_user_edit_educational_information(user=person.user, learning_unit_year_id=learning_unit_year.id). \
            is_valid()

    return False


def _is_tutor_summary_responsible_of_learning_unit_year(*, user, learning_unit_year_id, **kwargs):
    value = LearningUnitYear.objects.filter(pk=learning_unit_year_id, attribution__summary_responsible=True,
                                            attribution__tutor__person__user=user).exists()
    if not value:
        raise PermissionDenied(_("You are not summary responsible for this learning unit."))


def _is_learning_unit_year_summary_editable(*, learning_unit_year_id, **kwargs):
    value = LearningUnitYear.objects.filter(pk=learning_unit_year_id, summary_locked=False).exists()
    if not value:
        raise PermissionDenied(_("The learning unit is not summary editable."))


def _is_calendar_opened_to_edit_educational_information(*, learning_unit_year_id, **kwargs):
    submission_dates = find_educational_information_submission_dates_of_learning_unit_year(learning_unit_year_id)
    if not submission_dates:
        raise PermissionDenied(_("Not in period to edit educational information."))

    now = datetime.datetime.now(tz=get_tzinfo())
    value = convert_date_to_datetime(submission_dates["start_date"]) <= now <= \
        convert_date_to_datetime(submission_dates["end_date"])
    if not value:
        raise PermissionDenied(_("Not in period to edit educational information."))


def find_educational_information_submission_dates_of_learning_unit_year(learning_unit_year_id):
    requirement_entity_version = find_last_entity_version_by_learning_unit_year_id(
        learning_unit_year_id=learning_unit_year_id,
        entity_type=entity_container_year_link_type.REQUIREMENT_ENTITY
    )
    if requirement_entity_version is None:
        return {}

    return find_summary_course_submission_dates_for_entity_version(requirement_entity_version)


class can_user_edit_educational_information(BasePerm):
    predicates = (
        _is_tutor_summary_responsible_of_learning_unit_year,
        _is_learning_unit_year_summary_editable,
        _is_calendar_opened_to_edit_educational_information
    )


class can_learning_unit_year_educational_information_be_udpated(BasePerm):
    predicates = (
        _is_learning_unit_year_summary_editable,
    )


def is_year_editable(learning_unit_year, person, raise_exception):
    result = learning_unit_year.academic_year.year >= settings.YEAR_LIMIT_LUE_MODIFICATION
    msg = "{}.  {}".format(
        _("You can't modify learning unit under year : %(year)d") %
        {"year": settings.YEAR_LIMIT_LUE_MODIFICATION},
        _("Modifications should be made in EPC for year %(year)d") %
        {"year": learning_unit_year.academic_year.year},
    )
    can_raise_exception(raise_exception,
                        result,
                        msg)
    return result


def can_raise_exception(raise_exception, result, msg):
    if raise_exception and not result:
        raise PermissionDenied(msg)


def is_person_linked_to_entity_in_charge_of_lu(learning_unit_year, person, raise_exception=False):
    result = False
    if person:
        result = is_person_linked_to_entity_in_charge_of_learning_unit(learning_unit_year, person, raise_exception)

    can_raise_exception(
        raise_exception,
        result,
        MSG_ONLY_IF_YOUR_ARE_LINK_TO_ENTITY
        )
    return result


def is_not_container_type_course_dissertation_or_internship(learning_unit_year, person, raise_exception):
    result = negation(_is_container_type_course_dissertation_or_internship(learning_unit_year, person, raise_exception))
    can_raise_exception(
        raise_exception,
        result,
        _("This learning unit is not eligible for proposal creation/modification")
    )
    return result


def _is_container_type_course_dissertation_or_internship2(learning_unit_year, _, raise_exception):
    return \
        learning_unit_year.learning_container_year and \
        learning_unit_year.learning_container_year.container_type in FACULTY_UPDATABLE_CONTAINER_TYPES
