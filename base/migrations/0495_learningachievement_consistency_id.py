import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0494_auto_20200115_0952'),
    ]

    operations = [
        migrations.AddField(
            model_name='learningachievement',
            name='consistency_id',
            field=models.IntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)]),
        ),
        migrations.RunSQL(
            sql='UPDATE base_learningachievement SET consistency_id=base_learningachievement.order+1',
            reverse_sql=migrations.RunSQL.noop
        ),
    ]
