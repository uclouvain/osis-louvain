from __future__ import unicode_literals

from django.db import migrations

from base.models.enums.academic_calendar_type import AcademicCalendarTypes


def populate_data_year(apps, schema_editor):
    calendar_references_data_next_year = [
        AcademicCalendarTypes.TEACHING_CHARGE_APPLICATION.name,
        AcademicCalendarTypes.SUMMARY_COURSE_SUBMISSION.name,
        AcademicCalendarTypes.EDUCATION_GROUP_EDITION.name
    ]
    academic_calendar_mdl = apps.get_model("base", "AcademicCalendar")
    academic_year_mdl = apps.get_model("base", "AcademicYear")
    academic_calendar_items = academic_calendar_mdl.objects.all()

    for item in academic_calendar_items:
        if item.reference in calendar_references_data_next_year:
            next_academic_year = academic_year_mdl.objects.get(year=item.academic_year.year + 1)
            item.data_year = next_academic_year
        else:
            item.data_year = item.academic_year
        item.save()


def reverse_migration(apps, schema_editor):
    academic_calendar_mdl = apps.get_model("base", "AcademicCalendar")
    academic_calendar_items = academic_calendar_mdl.objects.all()

    for item in academic_calendar_items:
        item.data_year = None
        item.save()


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0474_academiccalendar_data_year'),
    ]

    operations = [
        migrations.RunPython(populate_data_year, reverse_migration),
    ]
