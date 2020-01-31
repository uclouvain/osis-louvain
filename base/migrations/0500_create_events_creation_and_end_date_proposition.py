from __future__ import unicode_literals

from datetime import date

from django.db import migrations

from base.models.enums import academic_calendar_type


def create_calendar_events_propositions(apps, schema_editor):
    data_years_to_create = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
    for year in data_years_to_create:
        academic_year_mdl = apps.get_model("base", "AcademicYear")
        academic_calendar_mdl = apps.get_model("base", "AcademicCalendar")

        try:
            anac = academic_year_mdl.objects.get(year=year)
            academic_calendar_mdl.objects.create(
                academic_year=anac,
                data_year=anac,
                title="Modification UE par gestionnaires centraux",
                description="Période de modification des UE par les gestionnaires centraux",
                start_date=date(year - 6, 9, 15),
                end_date=date(year + 1, 9, 14),
                highlight_title="Modification UE par gestionnaires centraux",
                reference=academic_calendar_type.LEARNING_UNIT_EDITION_CENTRAL_MANAGERS
            )
            academic_calendar_mdl.objects.create(
                academic_year=anac,
                data_year=anac,
                title="Propositions création / fin enseignmt gest centr",
                description="Période d'ouverture des propositions de création ou fin d'enseignement par les "
                            "gestionnaires centraux",
                start_date=date(year - 6, 9, 15),
                end_date=date(year + 1, 9, 14),
                highlight_title="Propositions création / fin enseignmt gest centr",
                reference=academic_calendar_type.CREATION_OR_END_DATE_PROPOSAL_CENTRAL_MANAGERS
            )
            academic_calendar_mdl.objects.create(
                academic_year=anac,
                data_year=anac,
                title="Propositions création / fin enseignmt gest fac",
                description="Période d'ouverture des propositions de création ou fin d'enseignement par les "
                            "gestionnaires facultaires",
                start_date=date(year - 6, 9, 15),
                end_date=date(year, 9, 14),
                highlight_title="Propositions création / fin enseignmt gest fac",
                reference=academic_calendar_type.CREATION_OR_END_DATE_PROPOSAL_FACULTY_MANAGERS
            )
            academic_calendar_mdl.objects.create(
                academic_year=anac,
                data_year=anac,
                title="Propositions modification / transformation central",
                description="Période d'ouverture des propositions de modification ou transformation par les "
                            "gestionnaires centraux",
                start_date=date(year - 1, 9, 15),
                end_date=date(year + 1, 9, 14),
                highlight_title="Propositions modif / transfo gest centr",
                reference=academic_calendar_type.MODIFICATION_OR_TRANSFORMATION_PROPOSAL_CENTRAL_MANAGERS
            )
            academic_calendar_mdl.objects.create(
                academic_year=anac,
                data_year=anac,
                title="Propositions modification / transformation fac",
                description="Période d'ouverture des propositions de modification ou transformation par les "
                            "gestionnaires facultaires",
                start_date=date(year - 1, 9, 15),
                end_date=date(year, 9, 14),
                highlight_title="Propositions modif / transfo gest fac",
                reference=academic_calendar_type.MODIFICATION_OR_TRANSFORMATION_PROPOSAL_FACULTY_MANAGERS
            )
        except academic_year_mdl.DoesNotExist:
            pass


def reverse_migration(apps, schema_editor):
    data_years_to_delete = [2019, 2020, 2021, 2022, 2023, 2024, 2025]
    academic_year_mdl = apps.get_model("base", "AcademicYear")
    academic_calendar_mdl = apps.get_model("base", "AcademicCalendar")
    for year in data_years_to_delete:
        try:
            anac = academic_year_mdl.objects.get(year=year)
            academic_calendar_mdl.objects.filter(
                academic_year=anac,
                data_year=anac,
                title="Modification UE par gestionnaires centraux",
                description="Période de modification des UE par les gestionnaires centraux",
                start_date=date(year - 6, 9, 15),
                end_date=date(year + 1, 9, 14),
                highlight_title="Modification UE par gestionnaires centraux",
                reference=academic_calendar_type.LEARNING_UNIT_EDITION_CENTRAL_MANAGERS
            ).delete()
            academic_calendar_mdl.objects.filter(
                academic_year=anac,
                data_year=anac,
                title="Propositions création / fin enseignmt gest centr",
                description="Période d'ouverture des propositions de création ou fin d'enseignement par les "
                            "gestionnaires centraux",
                start_date=date(year - 6, 9, 15),
                end_date=date(year + 1, 9, 14),
                highlight_title="Propositions création / fin enseignmt gest centr",
                reference=academic_calendar_type.CREATION_OR_END_DATE_PROPOSAL_CENTRAL_MANAGERS
            ).delete()
            academic_calendar_mdl.objects.filter(
                academic_year=anac,
                data_year=anac,
                title="Propositions création / fin enseignmt gest fac",
                description="Période d'ouverture des propositions de création ou fin d'enseignement par les "
                            "gestionnaires facultaires",
                start_date=date(year - 6, 9, 15),
                end_date=date(year, 9, 14),
                highlight_title="Propositions création / fin enseignmt gest fac",
                reference=academic_calendar_type.CREATION_OR_END_DATE_PROPOSAL_FACULTY_MANAGERS
            ).delete()
            academic_calendar_mdl.objects.filter(
                academic_year=anac,
                data_year=anac,
                title="Propositions modification / transformation central",
                description="Période d'ouverture des propositions de modification ou transformation par les "
                            "gestionnaires centraux",
                start_date=date(year - 1, 9, 15),
                end_date=date(year + 1, 9, 14),
                highlight_title="Propositions modif / transfo gest centr",
                reference=academic_calendar_type.MODIFICATION_OR_TRANSFORMATION_PROPOSAL_CENTRAL_MANAGERS
            ).delete()
            academic_calendar_mdl.objects.filter(
                academic_year=anac,
                data_year=anac,
                title="Propositions modification / transformation fac",
                description="Période d'ouverture des propositions de modification ou transformation par les "
                            "gestionnaires facultaires",
                start_date=date(year - 1, 9, 15),
                end_date=date(year, 9, 14),
                highlight_title="Propositions modif / transfo gest fac",
                reference=academic_calendar_type.MODIFICATION_OR_TRANSFORMATION_PROPOSAL_FACULTY_MANAGERS
            ).delete()
        except academic_year_mdl.DoesNotExist:
            pass


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0499_auto_20200108_1526'),
    ]

    operations = [
        migrations.RunPython(create_calendar_events_propositions, reverse_migration),
    ]
