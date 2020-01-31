from __future__ import unicode_literals

from django.db import migrations

from base.models.enums.education_group_types import TrainingType


def create_partial_title(apps, schema_editor):
    education_group_year_mdl = apps.get_model("base", "EducationGroupYear")
    education_group_years = education_group_year_mdl.objects.filter(
        academic_year__year__gte=2019,
        education_group_type__name__in=TrainingType.finality_types()
    )
    for education_group_year in education_group_years:
        if education_group_year.education_group_type.name in [TrainingType.MASTER_MA_120.name,
                                                              TrainingType.MASTER_MA_180_240.name]:
            education_group_year.partial_title = "Finalité approfondie"
            education_group_year.partial_title_english = "Research Focus"
        if education_group_year.education_group_type.name in [TrainingType.MASTER_MD_120.name,
                                                              TrainingType.MASTER_MD_180_240.name]:
            education_group_year.partial_title = "Finalité didactique"
            education_group_year.partial_title_english = "Teaching Focus"
        if education_group_year.education_group_type.name in [TrainingType.MASTER_MS_120.name,
                                                              TrainingType.MASTER_MS_180_240.name]:
            education_group_year.partial_title = "Finalité spécialisée"
            education_group_year.partial_title_english = "Professional Focus"
        education_group_year.save()


def reverse_migration(apps, schema_editor):
    education_group_year_mdl = apps.get_model("base", "EducationGroupYear")
    education_group_years = education_group_year_mdl.objects.filter(
        academic_year__year__gte=2019,
        education_group_type__name__in=TrainingType.finality_types()
    )
    for education_group_year in education_group_years:
        education_group_year.partial_title = ""
        education_group_year.partial_title_english = ""
        education_group_year.save()


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0501_auto_20200128_1134'),
    ]

    operations = [
        migrations.RunPython(create_partial_title, reverse_migration),
    ]
