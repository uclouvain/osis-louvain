from __future__ import unicode_literals

from django.db import migrations


def remove_prerequisites_without_item(apps, schema_editor):
    prerequisite_model = apps.get_model("base", "Prerequisite")
    prerequisite_model.objects.filter(prerequisiteitem__isnull=True).delete()


def reverse_migration(apps, schema_editor):
    pass  # No need to restore prerequisites having no prerequisite_item


class Migration(migrations.Migration):
    dependencies = [
        ('base', '0505_update_summary_submission_calendars'),
    ]

    operations = [
        migrations.RunPython(remove_prerequisites_without_item, reverse_migration),
    ]
