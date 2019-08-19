from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0466_auto_20190730_1101'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='person',
            options={'permissions': (('can_read_persons_roles', 'Can read persons roles'),)},
        ),
    ]
