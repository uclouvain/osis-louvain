from backoffice.celery import app as celery_app
from education_group.calendar.dissertation_submission_calendar import DissertationSubmissionCalendar
from education_group.calendar.education_group_extended_daily_management import \
    EducationGroupExtendedDailyManagementCalendar
from education_group.calendar.education_group_limited_daily_management import \
    EducationGroupLimitedDailyManagementCalendar
from education_group.calendar.education_group_preparation_calendar import EducationGroupPreparationCalendar
from education_group.calendar.education_group_switch_calendar import EducationGroupSwitchCalendar


@celery_app.task
def run() -> dict:
    EducationGroupPreparationCalendar.ensure_consistency_until_n_plus_6()
    EducationGroupExtendedDailyManagementCalendar.ensure_consistency_until_n_plus_6()
    EducationGroupLimitedDailyManagementCalendar.ensure_consistency_until_n_plus_6()
    EducationGroupSwitchCalendar.ensure_consistency_until_n_plus_6()
    DissertationSubmissionCalendar.ensure_consistency_until_n_plus_6()
    return {}
