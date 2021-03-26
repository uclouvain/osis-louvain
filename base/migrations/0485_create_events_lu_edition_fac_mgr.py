from __future__ import unicode_literals

from datetime import date

from django.db import migrations


def create_events_lu_edition_fac_mgr(apps, schema_editor):
    data_years_to_create = [2019, 2020, 2021]
    for year in data_years_to_create:
        academic_year_mdl = apps.get_model("base", "AcademicYear")
        academic_calendar_mdl = apps.get_model("base", "AcademicCalendar")

        try:
            anac = academic_year_mdl.objects.get(year=year)
            academic_calendar_mdl.objects.create(
                academic_year=anac,
                data_year=anac,
                title="Modification UE par gestionnaires facultaires",
                description="Période de modification des Unités d'Enseignement par les gestionnaires facultaires",
                start_date=date(year - 2, 9, 15),
                end_date=date(year + 1, 9, 14),
                highlight_title="Modification UE par gestionnaires facultaires",
                reference='LEARNING_UNIT_EDITION_FACULTY_MANAGERS'
            )
        except academic_year_mdl.DoesNotExist:
            pass


def reverse_migration(apps, schema_editor):
    data_years_to_delete = [2019, 2020, 2021]
    academic_year_mdl = apps.get_model("base", "AcademicYear")
    academic_calendar_mdl = apps.get_model("base", "AcademicCalendar")
    for year in data_years_to_delete:
        try:
            anac = academic_year_mdl.objects.get(year=year)
            academic_calendar_mdl.objects.filter(
                academic_year=anac,
                data_year=anac,
                title="Modification UE par gestionnaires facultaires",
                description="Période de modification des Unités d'Enseignement par les gestionnaires facultaires",
                start_date=date(year - 2, 9, 15),
                end_date=date(year + 1, 9, 14),
                highlight_title="Modification UE par gestionnaires facultaires",
                reference='LEARNING_UNIT_EDITION_FACULTY_MANAGERS'
            ).delete()
        except academic_year_mdl.DoesNotExist:
            pass


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0484_message_template_postponement'),
    ]

    operations = [
        migrations.RunPython(create_events_lu_edition_fac_mgr, reverse_migration),
    ]
