
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('parents', '0002_alter_parent_cnic'),
    ]

    operations = [
        migrations.AlterField(
            model_name='parent',
            name='cnic',
            field=models.CharField(blank=True, db_index=True, help_text='Format: XXXXX-XXXXXXX-X (Pakistani CNIC). Unique per parent when non-empty.', max_length=20, validators=[django.core.validators.RegexValidator(message='CNIC must be in the format XXXXX-XXXXXXX-X (5-7-1 digits).', regex='^\\d{5}-\\d{7}-\\d$')]),
        ),
        migrations.AddConstraint(
            model_name='parent',
            constraint=models.UniqueConstraint(condition=models.Q(('cnic', ''), _negated=True), fields=('cnic',), name='unique_parent_cnic_when_nonempty'),
        ),
    ]
