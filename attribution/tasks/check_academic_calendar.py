from attribution.calendar.application_courses_calendar import ApplicationCoursesCalendar
from backoffice.celery import app as celery_app


@celery_app.task
def run() -> dict:
    ApplicationCoursesCalendar.ensure_consistency_until_n_plus_6()
    return {}
