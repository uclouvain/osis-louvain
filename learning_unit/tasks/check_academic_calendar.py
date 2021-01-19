from backoffice.celery import app as celery_app
from learning_unit.calendar.learning_unit_force_majeur_summary_edition import \
    LearningUnitForceMajeurSummaryEditionCalendar
from learning_unit.calendar.learning_unit_summary_edition_calendar import LearningUnitSummaryEditionCalendar


@celery_app.task
def run() -> dict:
    LearningUnitSummaryEditionCalendar.ensure_consistency_until_n_plus_6()
    LearningUnitForceMajeurSummaryEditionCalendar.ensure_consistency_until_n_plus_6()
    return {}
