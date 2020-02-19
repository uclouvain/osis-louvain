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
import datetime

from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _
from waffle.models import Flag

from attribution.business.perms import _is_tutor_attributed_to_the_learning_unit
from base.business import event_perms
from base.business.institution import find_summary_course_submission_dates_for_entity_version
from base.models import proposal_learning_unit, tutor
from base.models.entity import Entity
from base.models.entity_version import EntityVersion
from base.models.enums import learning_container_year_types
from base.models.enums.proposal_state import ProposalState
from base.models.enums.proposal_type import ProposalType
from base.models.learning_unit_year import LearningUnitYear
from base.models.proposal_learning_unit import ProposalLearningUnit
from osis_common.utils.datetime import get_tzinfo, convert_date_to_datetime
from osis_common.utils.perms import conjunction, disjunction, negation, BasePerm

FACULTY_UPDATABLE_CONTAINER_TYPES = (learning_container_year_types.COURSE,
                                     learning_container_year_types.DISSERTATION,
                                     learning_container_year_types.INTERNSHIP)

PROPOSAL_CONSOLIDATION_ELIGIBLE_STATES = (ProposalState.ACCEPTED.name,
                                          ProposalState.REFUSED.name)

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
MSG_NO_RIGHTS_TO_CONSOLIDATE = _("You don't have the rights to consolidate")
MSG_PROPOSAL_NOT_IN_CONSOLIDATION_ELIGIBLE_STATES = _("Proposal not in eligible state for consolidation")
MSG_CAN_DELETE_ACCORDING_TO_TYPE = _("Can delete according to the type of the learning unit")
MSG_NOT_ELIGIBLE_TO_DELETE_LU = _("Not eligible to delete learning units")
MSG_NOT_ELIGIBLE_TO_CREATE_MODIFY_PROPOSAL = _("You are not eligible to create/modify proposal")
MSG_PROPOSAL_IS_ON_AN_OTHER_YEAR = _("You can't modify proposal which is on an other year")
MSG_NOT_ELIGIBLE_FOR_MODIFICATION_BECAUSE_OF_TYPE = _("This learning unit isn't eligible for modification because of "
                                                      "it's type")
MSG_CANNOT_UPDATE_EXTERNAL_UNIT_NOT_COGRADUATION = _("You can only edit co-graduation external learning units")
MSG_CANNOT_EDIT_BECAUSE_OF_PROPOSAL = _("You can't edit because the learning unit has proposal")
MSG_NOT_ELIGIBLE_TO_MODIFY_END_YEAR_PROPOSAL_ON_THIS_YEAR = _(
    "You are not allowed to change the end year for this academic year")
MSG_NOT_ELIGIBLE_TO_PUT_IN_PROPOSAL_ON_THIS_YEAR = _("You are not allowed to put in proposal for this academic year")
MSG_NOT_ELIGIBLE = _("You are not eligible to manage learning units")


def check_lu_permission(person, permission, raise_exception=False):
    result = person.user.has_perm(permission)
    if raise_exception and not result:
        raise PermissionDenied(_(MSG_NOT_ELIGIBLE).capitalize())
    return result


def is_external_learning_unit_cograduation(learning_unit_year, person, raise_exception):
    result = not hasattr(learning_unit_year, 'externallearningunityear') or \
             learning_unit_year.externallearningunityear.co_graduation
    can_raise_exception(
        raise_exception,
        result,
        MSG_CANNOT_UPDATE_EXTERNAL_UNIT_NOT_COGRADUATION,
    )
    return result


def is_eligible_for_modification(learning_unit_year, person, raise_exception=False):
    return \
        check_lu_permission(person, 'base.can_edit_learningunit', raise_exception) and \
        is_year_editable(learning_unit_year, raise_exception) and \
        _is_learning_unit_year_in_state_to_be_modified(learning_unit_year, person, raise_exception) and \
        is_person_linked_to_entity_in_charge_of_lu(learning_unit_year, person, raise_exception) and \
        is_external_learning_unit_cograduation(learning_unit_year, person, raise_exception) and \
        _check_proposal_edition(learning_unit_year, raise_exception)


def is_eligible_for_modification_end_date(learning_unit_year, person, raise_exception=False):
    return \
        check_lu_permission(person, 'base.can_edit_learningunit_date', raise_exception) and \
        is_year_editable(learning_unit_year, raise_exception) and \
        not (is_learning_unit_year_in_past(learning_unit_year, person, raise_exception)) and \
        is_eligible_for_modification(learning_unit_year, person, raise_exception) and \
        _is_person_eligible_to_modify_end_date_based_on_container_type(learning_unit_year, person, raise_exception) and\
        is_external_learning_unit_cograduation(learning_unit_year, person, raise_exception)


def is_eligible_to_create_partim(learning_unit_year, person, raise_exception=False):
    return conjunction(
        is_person_linked_to_entity_in_charge_of_lu,
        _is_learning_unit_year_in_state_to_create_partim,
        is_learning_unit_year_full,
        is_external_learning_unit_cograduation
    )(learning_unit_year, person, raise_exception)


def is_eligible_to_create_modification_proposal(learning_unit_year, person, raise_exception=False):
    result = \
        check_lu_permission(person, 'base.can_propose_learningunit', raise_exception) and \
        not(is_learning_unit_year_in_past(learning_unit_year, person, raise_exception))and \
        not(is_learning_unit_year_a_partim(learning_unit_year, person, raise_exception))and \
        _is_container_type_course_dissertation_or_internship(learning_unit_year, person, raise_exception)and \
        not(is_learning_unit_year_in_proposal(learning_unit_year, person, raise_exception))and \
        is_person_linked_to_entity_in_charge_of_learning_unit(learning_unit_year, person) and \
        is_external_learning_unit_cograduation(learning_unit_year, person, raise_exception)
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
        _has_person_the_right_to_make_proposal(proposal, person, raise_exception) and \
        is_external_learning_unit_cograduation(proposal.learning_unit_year, person, raise_exception)
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
        person.is_faculty_manager and \
        person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year)


def can_update_learning_achievement(learning_unit_year, person):
    flag = Flag.get('learning_achievement_update')
    return flag.is_active_for_user(person.user) and \
        person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year) and \
        is_year_editable(learning_unit_year, raise_exception=False)


def is_eligible_to_delete_learning_unit_year(learning_unit_year, person, raise_exception=False):
    msg = None
    checked_ok = \
        check_lu_permission(person, 'base.can_delete_learningunit', raise_exception) and \
        _can_delete_learning_unit_year_according_type(learning_unit_year, person, raise_exception)
    if not checked_ok:
        msg = MSG_NOT_ELIGIBLE_TO_DELETE_LU
    elif not person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year):
        msg = MSG_ONLY_IF_YOUR_ARE_LINK_TO_ENTITY
    elif learning_unit_year.is_prerequisite():
        msg = MSG_LEARNING_UNIT_IS_OR_HAS_PREREQUISITE
    elif LearningUnitYear.objects.filter(learning_unit=learning_unit_year.learning_unit,
                                         academic_year__year__lt=settings.YEAR_LIMIT_LUE_MODIFICATION):
        msg = _("You cannot delete a learning unit which is existing before %(limit_year)s") % {
            "limit_year": settings.YEAR_LIMIT_LUE_MODIFICATION}

    result = False if msg else True
    can_raise_exception(
        raise_exception,
        result,
        msg
    )

    return result


def _is_person_eligible_to_edit_proposal_based_on_state(proposal, person, raise_exception=False):
    if person.is_central_manager:
        return True
    elif person.is_faculty_manager:
        if proposal.state != ProposalState.FACULTY.name:
            can_raise_exception(
                raise_exception,
                False,
                MSG_NOT_PROPOSAL_STATE_FACULTY
            )
            return False

        if proposal.type == ProposalType.MODIFICATION.name and \
                not event_perms.generate_event_perm_modification_transformation_proposal(
                    person=person,
                    obj=proposal.learning_unit_year,
                    raise_exception=False
                ).is_open():
            can_raise_exception(
                raise_exception,
                False,
                MSG_PROPOSAL_IS_ON_AN_OTHER_YEAR
            )
            return False
        return True

    return False


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
    luy_container_type = learning_unit_year.learning_container_year.container_type
    return person.user.has_perm("base.can_manage_attribution") and \
        luy_container_type in learning_container_year_types.TYPE_ALLOWED_FOR_ATTRIBUTIONS and \
        person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year)


def _is_person_central_manager(_, person, raise_exception):
    return person.is_central_manager


def _is_learning_unit_year_a_partim(learning_unit_year, _, raise_exception=False):
    return learning_unit_year.is_partim()


def _is_person_in_accordance_with_proposal_state(proposal, person, raise_exception=False):
    result = person.is_central_manager or proposal.state == ProposalState.FACULTY.name
    can_raise_exception(
        raise_exception, result,
        MSG_PERSON_NOT_IN_ACCORDANCE_WITH_PROPOSAL_STATE
    )
    return result


def _has_person_the_right_to_make_proposal(_, person, raise_exception=False):
    result = person.user.has_perm('base.can_propose_learningunit')
    can_raise_exception(
        raise_exception, result,
        MSG_NOT_ELIGIBLE_TO_CREATE_MODIFY_PROPOSAL)
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


def _is_learning_unit_year_in_state_to_create_partim(learning_unit_year, person, raise_exception=False):
    business_check = (person.is_central_manager and not is_learning_unit_year_in_past(learning_unit_year, person)) or \
        (person.is_faculty_manager and learning_unit_year.learning_container_year)

    calendar_check = event_perms.generate_event_perm_learning_unit_edition(
        person=person,
        obj=learning_unit_year,
        raise_exception=False
    ).is_open()

    return business_check and calendar_check


def _is_learning_unit_year_in_state_to_be_modified(learning_unit_year, person, raise_exception):
    business_check = person.is_central_manager or learning_unit_year.learning_container_year

    calendar_check = event_perms.generate_event_perm_learning_unit_edition(
        person=person,
        obj=learning_unit_year,
        raise_exception=False
    ).is_open()

    result = business_check and calendar_check
    can_raise_exception(
        raise_exception,
        result,
        MSG_NOT_GOOD_RANGE_OF_YEARS,
        )
    return result


def _is_proposal_in_state_to_be_consolidated(proposal, _):
    return proposal.state in PROPOSAL_CONSOLIDATION_ELIGIBLE_STATES


def _can_delete_learning_unit_year_according_type(learning_unit_year, person, raise_exception=False):
    if not person.is_central_manager and person.is_faculty_manager:
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
    initial_container_year = learning_unit_proposal.initial_data.get("learning_container_year")
    if not initial_container_year:
        return False
    requirement_entity = initial_container_year.get('requirement_entity')
    if not requirement_entity:
        return False
    return a_person.is_attached_entities(Entity.objects.filter(pk=requirement_entity))


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
    if is_year_editable(learning_unit_year, raise_exception=False):
        # Case faculty/central: We need to check if user is linked to entity
        if person.is_faculty_manager or person.is_central_manager:
            return person.is_linked_to_entity_in_charge_of_learning_unit_year(learning_unit_year)

        # Case Tutor: We need to check if today is between submission date
        if tutor.is_tutor(person.user):
            return can_user_edit_educational_information(
                user=person.user,
                learning_unit_year_id=learning_unit_year.id
            ).is_valid()

    return False


def _is_tutor_summary_responsible_of_learning_unit_year(*, user, learning_unit_year_id, **kwargs):
    if not _is_tutor_attributed_to_the_learning_unit(user, learning_unit_year_id):
        raise PermissionDenied(_("You are not attributed to this learning unit."))


def _is_learning_unit_year_summary_editable(*, learning_unit_year_id, **kwargs):
    if isinstance(learning_unit_year_id, LearningUnitYear):
        value = True
    else:
        value = LearningUnitYear.objects.filter(pk=learning_unit_year_id, summary_locked=False).exists()

    if not value:
        raise PermissionDenied(_("The learning unit's description fiche is not editable."))


def _is_calendar_opened_to_edit_educational_information(*, learning_unit_year_id, **kwargs):
    submission_dates = find_educational_information_submission_dates_of_learning_unit_year(learning_unit_year_id)
    permission_denied_msg = _("Not in period to edit description fiche.")
    if not submission_dates:
        raise PermissionDenied(permission_denied_msg)

    now = datetime.datetime.now(tz=get_tzinfo())
    value = convert_date_to_datetime(submission_dates["start_date"]) <= now <= \
        convert_date_to_datetime(submission_dates["end_date"])
    if not value:
        raise PermissionDenied(permission_denied_msg)


def find_educational_information_submission_dates_of_learning_unit_year(learning_unit_year_id):
    requirement_entity_version = find_last_requirement_entity_version(
        learning_unit_year_id=learning_unit_year_id,
    )
    if requirement_entity_version is None:
        return {}

    return find_summary_course_submission_dates_for_entity_version(
        entity_version=requirement_entity_version,
        ac_year=LearningUnitYear.objects.get(pk=learning_unit_year_id).academic_year
    )


def find_last_requirement_entity_version(learning_unit_year_id):
    now = datetime.datetime.now(get_tzinfo())
    # TODO :: merge code below to get only 1 hit on database
    requirement_entity_id = LearningUnitYear.objects.filter(
        pk=learning_unit_year_id
    ).select_related(
        'learning_container_year'
    ).only(
        'learning_container_year'
    ).get().learning_container_year.requirement_entity_id
    try:
        return EntityVersion.objects.current(now).filter(entity=requirement_entity_id).get()
    except EntityVersion.DoesNotExist:
        return None


class can_user_edit_educational_information(BasePerm):
    predicates = (
        _is_tutor_summary_responsible_of_learning_unit_year,
        _is_learning_unit_year_summary_editable,
        _is_calendar_opened_to_edit_educational_information
    )


def is_year_editable(learning_unit_year, raise_exception):
    result = learning_unit_year.academic_year.year > settings.YEAR_LIMIT_LUE_MODIFICATION
    msg = "{}.  {}".format(
        _("You can't modify learning unit under year : %(year)d") %
        {"year": settings.YEAR_LIMIT_LUE_MODIFICATION + 1},
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
        result = is_person_linked_to_entity_in_charge_of_learning_unit(learning_unit_year, person)

    can_raise_exception(
        raise_exception,
        result,
        MSG_ONLY_IF_YOUR_ARE_LINK_TO_ENTITY
        )
    return result


def _is_container_type_course_dissertation_or_internship2(learning_unit_year, _, raise_exception):
    return \
        learning_unit_year.learning_container_year and \
        learning_unit_year.learning_container_year.container_type in FACULTY_UPDATABLE_CONTAINER_TYPES


def _check_proposal_edition(learning_unit_year, raise_exception):
    result = not ProposalLearningUnit.objects.filter(
        learning_unit_year__learning_unit=learning_unit_year.learning_unit,
        learning_unit_year__academic_year__year__lte=learning_unit_year.academic_year.year
    ).exists()

    can_raise_exception(
        raise_exception,
        result,
        MSG_CANNOT_EDIT_BECAUSE_OF_PROPOSAL,
    )
    return result


def is_eligible_to_modify_end_year_by_proposal(learning_unit_year, person, raise_exception=False):
    result = is_eligible_to_create_modification_proposal(learning_unit_year, person, raise_exception)
    if result:
        return can_modify_end_year_by_proposal(learning_unit_year, person, raise_exception)
    else:
        can_raise_exception(
            raise_exception,
            result,
            MSG_CANNOT_EDIT_BECAUSE_OF_PROPOSAL,
        )
        return result


def can_modify_end_year_by_proposal(learning_unit_year, person, raise_exception=False):
    result = event_perms.generate_event_perm_creation_end_date_proposal(
        person=person,
        obj=learning_unit_year,
        raise_exception=False
    ).is_open()

    can_raise_exception(
        raise_exception,
        result,
        MSG_NOT_ELIGIBLE_TO_MODIFY_END_YEAR_PROPOSAL_ON_THIS_YEAR
    )
    return result


def is_eligible_to_modify_by_proposal(learning_unit_year, person, raise_exception=False):
    result = is_eligible_to_create_modification_proposal(learning_unit_year, person, raise_exception)

    if result:
        return can_modify_by_proposal(learning_unit_year, person, raise_exception)
    else:
        can_raise_exception(
            raise_exception,
            result,
            MSG_CANNOT_EDIT_BECAUSE_OF_PROPOSAL,
        )
        return result


def can_modify_by_proposal(learning_unit_year, person, raise_exception=False):
    result = event_perms.generate_event_perm_modification_transformation_proposal(
        person=person,
        obj=learning_unit_year,
        raise_exception=False
    ).is_open()

    can_raise_exception(
        raise_exception, result, MSG_NOT_ELIGIBLE_TO_PUT_IN_PROPOSAL_ON_THIS_YEAR
    )
    return result


def is_person_linked_to_entity_in_charge_of_learning_unit(learning_unit_year, person):
    requirement_entity = learning_unit_year.learning_container_year.requirement_entity
    if not requirement_entity:
        return False
    return person.is_attached_entities([requirement_entity])
