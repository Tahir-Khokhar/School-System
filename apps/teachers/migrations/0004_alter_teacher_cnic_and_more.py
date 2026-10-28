
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0003_alter_teacher_cnic_alter_teacher_gender_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacher',
            name='cnic',
            field=models.CharField(blank=True, db_index=True, help_text='Format: XXXXX-XXXXXXX-X (Pakistani CNIC). Unique per teacher when non-empty.', max_length=20),
        ),
        migrations.AddConstraint(
            model_name='teacher',
            constraint=models.UniqueConstraint(condition=models.Q(('cnic', ''), _negated=True), fields=('cnic',), name='unique_teacher_cnic_when_nonempty'),
        ),
    ]
