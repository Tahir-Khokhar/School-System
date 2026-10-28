
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0002_alter_student_cnic_or_bform_alter_student_photograph'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='cnic_or_bform',
            field=models.CharField(blank=True, db_index=True, help_text='CNIC for adults or B-Form for minors. Unique per student when non-empty.', max_length=20),
        ),
        migrations.AddConstraint(
            model_name='student',
            constraint=models.UniqueConstraint(condition=models.Q(('cnic_or_bform', ''), _negated=True), fields=('cnic_or_bform',), name='unique_student_cnic_when_nonempty'),
        ),
    ]
