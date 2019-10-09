from datetime import datetime

from celery.schedules import crontab

from backoffice.celery import app as celery_app
from base.business.education_groups.automatic_postponement import EducationGroupAutomaticPostponementToN6, \
    ReddotEducationGroupAutomaticPostponement
from base.business.learning_units.automatic_postponement import LearningUnitAutomaticPostponementToN6
from base.models.academic_calendar import AcademicCalendar
from base.models.education_group_year import EducationGroupYear
from base.models.enums.academic_calendar_type import EDUCATION_GROUP_EDITION

celery_app.conf.beat_schedule.update({
    'Extend learning units': {
        'task': 'base.tasks.extend_learning_units',
        'schedule': crontab(minute=0, hour=0, day_of_month=15, month_of_year=7)
    },
    'Extend education groups': {
        'task': 'base.tasks.extend_education_groups',
        'schedule': crontab(minute=0, hour=2, day_of_month=15, month_of_year=7)
    },
    'Check academic calendar': {
        'task': 'base.tasks.check_academic_calendar',
        'schedule': crontab(minute=0, hour=1)
    },
})


@celery_app.task
def extend_learning_units():
    process = LearningUnitAutomaticPostponementToN6()
    process.postpone()
    return process.serialize_postponement_results()


@celery_app.task
def extend_education_groups():
    process = EducationGroupAutomaticPostponementToN6()
    process.postpone()
    return process.serialize_postponement_results()


@celery_app.task
def check_academic_calendar() -> dict:
    open_calendar = AcademicCalendar.objects.filter(start_date=datetime.now().date()).first()
    if open_calendar and open_calendar.reference == EDUCATION_GROUP_EDITION:
        # Copy the education group data of the open academic year.
        process = ReddotEducationGroupAutomaticPostponement(
            EducationGroupYear.objects.filter(academic_year=open_calendar.academic_year)
        )
        process.postpone()
        return {"Copy of Reddot data": process.serialize_postponement_results()}

    return {}
