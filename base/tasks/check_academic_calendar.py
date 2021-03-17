from datetime import datetime

from backoffice.celery import app as celery_app
from base.business.education_groups.automatic_postponement import ReddotEducationGroupAutomaticPostponement
from base.models.academic_calendar import AcademicCalendar
from base.models.education_group_year import EducationGroupYear
from base.models.enums.academic_calendar_type import EDUCATION_GROUP_EDITION


@celery_app.task
def run() -> dict:
    open_calendar = AcademicCalendar.objects.filter(start_date=datetime.now().date()).first()
    if open_calendar and open_calendar.reference == EDUCATION_GROUP_EDITION:
        # Copy the education group data of the open academic year.
        process = ReddotEducationGroupAutomaticPostponement(
            EducationGroupYear.objects.filter(academic_year=open_calendar.data_year)
        )
        process.postpone()
        return {"Copy of Reddot data": process.serialize_postponement_results()}
    return {}
