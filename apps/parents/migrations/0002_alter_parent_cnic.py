
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parents', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parent',
            name='cnic',
            field=models.CharField(blank=True, db_index=True, help_text='Format: XXXXX-XXXXXXX-X (Pakistani CNIC).', max_length=20, unique=True, validators=[django.core.validators.RegexValidator(message='CNIC must be in the format XXXXX-XXXXXXX-X (5-7-1 digits).', regex='^\\d{5}-\\d{7}-\\d$')]),
        ),
    ]
