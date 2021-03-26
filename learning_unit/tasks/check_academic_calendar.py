from backoffice.celery import app as celery_app
from learning_unit.calendar.learning_unit_enrollment_calendar import LearningUnitEnrollmentCalendar
from learning_unit.calendar.learning_unit_force_majeur_summary_edition import \
    LearningUnitForceMajeurSummaryEditionCalendar
from learning_unit.calendar.learning_unit_summary_edition_calendar import LearningUnitSummaryEditionCalendar
from learning_unit.calendar.learning_unit_extended_proposal_management import \
    LearningUnitExtendedProposalManagementCalendar
from learning_unit.calendar.learning_unit_limited_proposal_management import \
    LearningUnitLimitedProposalManagementCalendar


@celery_app.task
def run() -> dict:
    LearningUnitSummaryEditionCalendar.ensure_consistency_until_n_plus_6()
    LearningUnitForceMajeurSummaryEditionCalendar.ensure_consistency_until_n_plus_6()
    LearningUnitEnrollmentCalendar.ensure_consistency_until_n_plus_6()
    LearningUnitExtendedProposalManagementCalendar.ensure_consistency_until_n_plus_6()
    LearningUnitLimitedProposalManagementCalendar.ensure_consistency_until_n_plus_6()
    return {}
