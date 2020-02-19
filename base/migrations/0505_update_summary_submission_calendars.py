from __future__ import unicode_literals

import datetime

from django.db import migrations

from base.models.enums.academic_calendar_type import SUMMARY_COURSE_SUBMISSION


def update_summary_submission_calendars(apps, schema_editor):
    academic_calendar_mdl = apps.get_model("base", "AcademicCalendar")
    academic_calendar_items = academic_calendar_mdl.objects.filter(reference=SUMMARY_COURSE_SUBMISSION)

    for item in academic_calendar_items:
        item.data_year = item.academic_year
        item.start_date = datetime.date(item.academic_year.year, 6, 15)
        item.end_date = datetime.date(item.academic_year.year, 9, 13)
        item.save()


def reverse_migration(apps, schema_editor):
    academic_year_mdl = apps.get_model("base", "AcademicYear")
    academic_calendar_mdl = apps.get_model("base", "AcademicCalendar")
    academic_calendar_items = academic_calendar_mdl.objects.filter(reference=SUMMARY_COURSE_SUBMISSION)

    for item in academic_calendar_items:
        next_academic_year = academic_year_mdl.objects.get(year=item.academic_year.year + 1)
        item.data_year = next_academic_year
        item.save()


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0504_auto_20200203_1441'),
    ]

    operations = [
        migrations.RunPython(update_summary_submission_calendars, reverse_migration),
    ]
