from django.conf import settings
from django.utils.translation import gettext_lazy as _
from rules import predicate

from attribution.models.attribution_charge_new import AttributionChargeNew
from attribution.models.tutor_application import TutorApplication
from base.models.enums import learning_container_year_types as container_types, learning_container_year_types
from base.models.enums.learning_container_year_types import LearningContainerYearType
from base.models.enums.proposal_state import ProposalState
from base.models.enums.proposal_type import ProposalType
from base.models.proposal_learning_unit import ProposalLearningUnit
from education_group.calendar.education_group_extended_daily_management import \
    EducationGroupExtendedDailyManagementCalendar
from education_group.calendar.education_group_limited_daily_management import \
    EducationGroupLimitedDailyManagementCalendar
from learning_unit.calendar.learning_unit_extended_proposal_management import \
    LearningUnitExtendedProposalManagementCalendar
from learning_unit.calendar.learning_unit_force_majeur_summary_edition import \
    LearningUnitForceMajeurSummaryEditionCalendar
from learning_unit.calendar.learning_unit_limited_proposal_management import \
    LearningUnitLimitedProposalManagementCalendar
from learning_unit.calendar.learning_unit_summary_edition_calendar import LearningUnitSummaryEditionCalendar
from osis_role.cache import predicate_cache
from osis_role.errors import predicate_failed_msg

FACULTY_EDITABLE_CONTAINER_TYPES = (
    LearningContainerYearType.COURSE,
    LearningContainerYearType.DISSERTATION,
    LearningContainerYearType.INTERNSHIP
)

FACULTY_DATE_EDITABLE_CONTAINER_TYPES = (
    LearningContainerYearType.OTHER_INDIVIDUAL,
    LearningContainerYearType.OTHER_COLLECTIVE,
    LearningContainerYearType.MASTER_THESIS,
    LearningContainerYearType.EXTERNAL
)

PROPOSAL_CONSOLIDATION_ELIGIBLE_STATES = (ProposalState.ACCEPTED.name, ProposalState.REFUSED.name)

DELETABLE_CONTAINER_TYPES = [LearningContainerYearType.DISSERTATION, LearningContainerYearType.INTERNSHIP]


@predicate(bind=True)
@predicate_failed_msg(message=_("You can only modify a learning unit when your are linked to its requirement entity"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_user_attached_to_requirement_entity(self, user, learning_unit_year=None):
    if learning_unit_year:
        initial_container_year = learning_unit_year.learning_container_year
        requirement_entity_id = initial_container_year.requirement_entity
        return _is_attached_to_entity(requirement_entity_id, self)
    return learning_unit_year


@predicate(bind=True)
@predicate_failed_msg(message=_("You can only modify a learning unit when your are linked to its requirement entity"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_user_attached_to_current_requirement_entity(self, user, learning_unit_year=None):
    if learning_unit_year:
        current_container_year = learning_unit_year.learning_container_year
        return current_container_year is not None and _is_attached_to_entity(
            current_container_year.requirement_entity_id, self
        )
    return learning_unit_year


def _is_attached_to_entity(requirement_entity, self):
    user_entity_ids = self.context['role_qs'].get_entities_ids()
    return requirement_entity in user_entity_ids


@predicate(bind=True)
@predicate_failed_msg(
    message=_(
        "You can't modify learning unit under year : %(year)d. Modifications should be made in EPC under year %(year)d"
    ) % {"year": settings.YEAR_LIMIT_LUE_MODIFICATION + 1},
)
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_year_older_or_equals_than_limit_settings_year(self, user, learning_unit_year=None):
    if learning_unit_year:
        return learning_unit_year.academic_year.year >= settings.YEAR_LIMIT_LUE_MODIFICATION
    return None


@predicate(bind=True)
@predicate_failed_msg(
    message=_("The learning unit start year is set before %(year)d.") % {
        "year": settings.YEAR_LIMIT_LUE_MODIFICATION + 1
    },
)
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_start_year_after_year_limit(self, user, learning_unit_year=None):
    if learning_unit_year:
        learning_unit = learning_unit_year.learning_unit
        return learning_unit.start_year.year > settings.YEAR_LIMIT_LUE_MODIFICATION
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("You cannot delete a learning unit which is prerequisite or has prerequisite(s)"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def has_learning_unit_prerequisite_dependencies(self, user, learning_unit_year):
    if learning_unit_year:
        return not learning_unit_year.is_prerequisite()
    return None


@predicate(bind=True)
@predicate_failed_msg(
    message=_(
        "Learning unit type is not deletable because it is either a full course or it has the following type: %(types)s"
    ) % {"types": [type.value for type in DELETABLE_CONTAINER_TYPES]}
)
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_container_type_deletable(self, user, learning_unit_year):
    if learning_unit_year:
        if learning_unit_year.is_partim():
            return True
        container_type = learning_unit_year.learning_container_year.container_type
        is_full_course = container_type == container_types.COURSE and learning_unit_year.is_full()
        type_is_deletable = container_type not in [type.name for type in DELETABLE_CONTAINER_TYPES]
        return not is_full_course and type_is_deletable
    return None


@predicate(bind=True)
@predicate_failed_msg(
    message=_(
        "This learning unit isn't eligible for modification because of its type which is not among those types:"
        " %(types)s"
    ) % {"types": [type.value for type in FACULTY_EDITABLE_CONTAINER_TYPES]}
)
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_container_type_editable(self, user, learning_unit_year):
    if learning_unit_year:
        container = learning_unit_year.learning_container_year
        return container and container.container_type in [type.name for type in FACULTY_EDITABLE_CONTAINER_TYPES]
    return None


@predicate(bind=True)
@predicate_failed_msg(
    message=_(
        "The learning unit date is not eligible for modification because of its type which is not among those types:"
        " %(types)s"
    ) % {"types": [type.value for type in FACULTY_DATE_EDITABLE_CONTAINER_TYPES]}
)
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_date_container_type_editable(self, user, learning_unit_year):
    if learning_unit_year:
        container = learning_unit_year.learning_container_year
        return container and container.container_type in [type.name for type in FACULTY_DATE_EDITABLE_CONTAINER_TYPES]
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("This learning unit is not editable this period."))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_edition_for_central_manager_period_open(self, user, learning_unit_year):
    calendar = EducationGroupExtendedDailyManagementCalendar()
    if learning_unit_year:
        return calendar.is_target_year_authorized(target_year=learning_unit_year.academic_year.year)
    return bool(calendar.get_target_years_opened())


@predicate(bind=True)
@predicate_failed_msg(message=_("This learning unit is not editable this period."))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_edition_for_faculty_manager_period_open(self, user, learning_unit_year):
    calendar = EducationGroupLimitedDailyManagementCalendar()
    if learning_unit_year:
        return calendar.is_target_year_authorized(target_year=learning_unit_year.academic_year.year)
    return bool(calendar.get_target_years_opened())


@predicate(bind=True)
@predicate_failed_msg(message=_("You are not allowed to create proposal during this academic year"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_proposal_creation_period_open(self, user, group_year: 'GroupYear' = None):
    calendar = LearningUnitLimitedProposalManagementCalendar()
    if group_year:
        return calendar.is_target_year_authorized(target_year=group_year.academic_year.year)
    return bool(calendar.get_target_years_opened())


@predicate(bind=True)
@predicate_failed_msg(message=_("You are not allowed to put in proposal for ending date during this academic year"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_proposal_date_edition_period_open(self, user, group_year: 'GroupYear' = None):
    calendar = LearningUnitLimitedProposalManagementCalendar()
    if group_year:
        return calendar.is_target_year_authorized(target_year=group_year.academic_year.year)
    return bool(calendar.get_target_years_opened())


@predicate(bind=True)
@predicate_failed_msg(message=_("You are not allowed to put in proposal for modification during this academic year"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_proposal_edition_period_open(self, user, group_year: 'GroupYear' = None):
    calendar = LearningUnitLimitedProposalManagementCalendar()
    if group_year:
        return calendar.is_target_year_authorized(target_year=group_year.academic_year.year)
    return bool(calendar.get_target_years_opened())


@predicate(bind=True)
@predicate_failed_msg(message=_("You are not allowed to manage proposal during this academic year"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_proposal_extended_management_calendar_open(self, user, group_year: 'GroupYear' = None):
    calendar = LearningUnitExtendedProposalManagementCalendar()
    if group_year:
        return calendar.is_target_year_authorized(target_year=group_year.academic_year.year)
    return bool(calendar.get_target_years_opened())


@predicate(bind=True)
@predicate_failed_msg(message=_("Not in period to edit description fiche."))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_summary_edition_calendar_open(self, user, learning_unit_year):
    calendar = LearningUnitSummaryEditionCalendar()
    if learning_unit_year:
        return calendar.is_target_year_authorized(target_year=learning_unit_year.academic_year.year)
    return bool(calendar.get_target_years_opened())


@predicate(bind=True)
@predicate_failed_msg(message=_("Not in period to edit force majeure section."))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_force_majeur_summary_edition_calendar_open(self, user, learning_unit_year):
    calendar = LearningUnitForceMajeurSummaryEditionCalendar()
    if learning_unit_year:
        return calendar.is_target_year_authorized(target_year=learning_unit_year.academic_year.year)
    return bool(calendar.get_target_years_opened())


@predicate(bind=True)
@predicate_failed_msg(message=_("Learning unit is not full"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_year_full(self, user, learning_unit_year):
    if learning_unit_year:
        return learning_unit_year.is_full()
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("You can only edit co-graduation external learning units"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_external_learning_unit_with_cograduation(self, user, learning_unit_year):
    if learning_unit_year and hasattr(learning_unit_year, 'externallearningunityear'):
        return learning_unit_year.externallearningunityear.co_graduation
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("You cannot modify a learning unit of a previous year"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_year_not_in_past(self, user, learning_unit_year):
    if learning_unit_year:
        return not learning_unit_year.is_past()
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("The learning unit is a partim"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_year_not_a_partim(self, user, learning_unit_year):
    if learning_unit_year:
        return not learning_unit_year.is_partim()
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("The learning unit is not a partim"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_year_a_partim(self, user, learning_unit_year):
    if learning_unit_year:
        return learning_unit_year.is_partim()
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("The learning unit is not in proposal state"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_in_proposal_state(self, user, learning_unit_year):
    if learning_unit_year:
        return ProposalLearningUnit.objects.filter(
            learning_unit_year__learning_unit=learning_unit_year.learning_unit,
            learning_unit_year__academic_year__year__lte=learning_unit_year.academic_year.year
        ).exists()
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("The proposal is not on this academic year"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_year_in_proposal_state(self, user, learning_unit_year):
    if learning_unit_year:
        return ProposalLearningUnit.objects.filter(
            learning_unit_year__learning_unit=learning_unit_year.learning_unit,
            learning_unit_year__academic_year__year=learning_unit_year.academic_year.year
        ).exists()
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("The learning unit has proposal for this or a previous year"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_not_in_proposal_state_for_this_and_previous_years(self, user, learning_unit_year):
    if learning_unit_year:
        return not ProposalLearningUnit.objects.filter(
            learning_unit_year__learning_unit=learning_unit_year.learning_unit,
            learning_unit_year__academic_year__year__lte=learning_unit_year.academic_year.year
        ).exists()
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("The learning unit has proposal for this or any other year"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_not_in_proposal_state_any_year(self, user, learning_unit_year):
    if learning_unit_year:
        return not ProposalLearningUnit.objects.filter(
            learning_unit_year__learning_unit=learning_unit_year.learning_unit
        ).exists()
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("Person not in accordance with proposal state"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def has_faculty_proposal_state(self, user, learning_unit_year):
    if learning_unit_year and hasattr(learning_unit_year, 'proposallearningunit'):
        return learning_unit_year.proposallearningunit.state == ProposalState.FACULTY.name
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("This learning unit is not of type creation"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_proposal_of_type_creation(self, user, learning_unit_year):
    if learning_unit_year and hasattr(learning_unit_year, 'proposallearningunit'):
        return learning_unit_year.proposallearningunit.type == ProposalType.CREATION.name
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("This learning unit is not of type modification"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_proposal_of_type_modification(self, user, learning_unit_year):
    if learning_unit_year and hasattr(learning_unit_year, 'proposallearningunit'):
        return learning_unit_year.proposallearningunit.type == ProposalType.MODIFICATION.name
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("This learning unit is not of type suppression"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_proposal_of_type_suppression(self, user, learning_unit_year):
    if learning_unit_year and hasattr(learning_unit_year, 'proposallearningunit'):
        return learning_unit_year.proposallearningunit.type == ProposalType.SUPPRESSION.name
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("This learning unit is of type creation"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_not_proposal_of_type_creation(self, user, learning_unit_year):
    if learning_unit_year and hasattr(learning_unit_year, 'proposallearningunit'):
        return learning_unit_year.proposallearningunit.type != ProposalType.CREATION.name
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("This learning unit has application this year"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def has_learning_unit_no_application_this_year(self, user, learning_unit_year):
    if learning_unit_year:
        learning_container_year = learning_unit_year.learning_container_year
        return not TutorApplication.objects.filter(learning_container_year=learning_container_year).exists()


@predicate(bind=True)
@predicate_failed_msg(message=_("This learning unit has application"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def has_learning_unit_no_application_all_years(self, user, learning_unit_year):
    if learning_unit_year and learning_unit_year.is_full():
        learning_container = learning_unit_year.learning_container_year.learning_container
        return not TutorApplication.objects.filter(
            learning_container_year__learning_container=learning_container
        ).exists()


@predicate(bind=True)
@predicate_failed_msg(message=_("This learning unit has teachers"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def has_learning_unit_partim_no_application_all_years(self, user, learning_unit_year):
    if learning_unit_year and learning_unit_year.is_partim():
        return not AttributionChargeNew.objects.filter(
            learning_component_year__learning_unit_year__learning_unit=learning_unit_year.learning_unit,
        ).exists()


@predicate(bind=True)
@predicate_failed_msg(message=_("This learning unit has an application in the future"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def has_learning_unit_no_application_in_future(self, user, learning_unit_year):
    if learning_unit_year:
        learning_container = learning_unit_year.learning_container_year.learning_container
        return not TutorApplication.objects.filter(
            learning_container_year__learning_container=learning_container,
            learning_container_year__academic_year__year__gt=learning_unit_year.academic_year.year
        ).exists()


@predicate(bind=True)
@predicate_failed_msg(message=_("This learning unit has an attribution in the future"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def has_learning_unit_no_attribution_in_future(self, user, learning_unit_year):
    if learning_unit_year:
        return not AttributionChargeNew.objects.filter(
            learning_component_year__learning_unit_year__learning_unit=learning_unit_year.learning_unit,
            learning_component_year__learning_unit_year__academic_year__year__gt=learning_unit_year.academic_year.year
        ).exists()


@predicate(bind=True)
@predicate_failed_msg(message=_("Proposal not in eligible state for consolidation"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_proposal_in_state_to_be_consolidated(self, user, learning_unit_year):
    if learning_unit_year and hasattr(learning_unit_year, 'proposallearningunit'):
        return learning_unit_year.proposallearningunit.state in PROPOSAL_CONSOLIDATION_ELIGIBLE_STATES
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("Proposal is of modification type"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_not_modification_proposal_type(self, user, learning_unit_year):
    if learning_unit_year and hasattr(learning_unit_year, 'proposallearningunit'):
        return learning_unit_year.proposallearningunit.type != ProposalType.MODIFICATION.name
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("Learning unit type is not allowed for attributions"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_type_allowed_for_attributions(self, user, learning_unit_year):
    if learning_unit_year:
        container_type = learning_unit_year.learning_container_year.container_type
        return container_type in learning_container_year_types.TYPE_ALLOWED_FOR_ATTRIBUTIONS
    return None


# TODO : remove this predicate after class refactoring because a learning unit will always have a container
@predicate(bind=True)
@predicate_failed_msg(message=_("You cannot edit this type of learning unit"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_with_container(self, user, learning_unit_year):
    if learning_unit_year:
        return learning_unit_year.learning_container_year
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("This learning unit has attribution this year"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def has_learning_unit_no_attribution_this_year(self, user, learning_unit_year):
    if learning_unit_year:
        learning_container_year = learning_unit_year.learning_container_year
        return not AttributionChargeNew.objects.filter(
            learning_component_year__learning_unit_year__learning_container_year=learning_container_year
        ).exists()
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("This learning unit has attribution"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def has_learning_unit_no_attribution_all_years(self, user, learning_unit_year):
    if learning_unit_year:
        learning_container = learning_unit_year.learning_container_year.learning_container
        return not AttributionChargeNew.objects.filter(
            learning_component_year__learning_unit_year__learning_container_year__learning_container=learning_container
        ).exists()
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("This learning unit is of type suppression"))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_not_proposal_of_type_suppression(self, user, learning_unit_year):
    if learning_unit_year and hasattr(learning_unit_year, 'proposallearningunit'):
        return learning_unit_year.proposallearningunit.type != ProposalType.SUPPRESSION.name
    return None


@predicate(bind=True)
@predicate_failed_msg(message=_("The learning unit's description fiche is not editable."))
@predicate_cache(cache_key_fn=lambda obj: getattr(obj, 'pk', None))
def is_learning_unit_year_summary_editable(self, user, learning_unit_year):
    if learning_unit_year:
        return not learning_unit_year.summary_locked
    return None
