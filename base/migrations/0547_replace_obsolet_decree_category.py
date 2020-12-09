from django.db import migrations

from base.models.enums.decree_category import DecreeCategories


def replace_aess_by_aessb(apps, schema_editor):
    EducationGroupYear = apps.get_model('base', 'EducationGroupYear')
    obsolet_egys = EducationGroupYear.objects.filter(
        decree_category='AESS'
    )
    for egy in obsolet_egys:
        egy.decree_category = DecreeCategories.AESSB.name
        egy.save()


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0546_auto_20201207_1024'),
    ]

    operations = [
        migrations.RunPython(replace_aess_by_aessb),
    ]
