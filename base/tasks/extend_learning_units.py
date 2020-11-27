from backoffice.celery import app as celery_app
from base.business.learning_units.automatic_postponement import LearningUnitAutomaticPostponementToN6


@celery_app.task
def run():
    process = LearningUnitAutomaticPostponementToN6()
    process.postpone()
    return process.serialize_postponement_results()
