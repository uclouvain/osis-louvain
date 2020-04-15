from django.contrib.postgres.operations import CreateExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0508_auto_20200325_1013'),
    ]

    operations = [
        CreateExtension("postgis"),
    ]
