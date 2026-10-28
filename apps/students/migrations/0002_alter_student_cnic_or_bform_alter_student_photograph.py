
import apps.common.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('students', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='student',
            name='cnic_or_bform',
            field=models.CharField(blank=True, db_index=True, help_text='CNIC for adults or B-Form for minors. Unique per student.', max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='photograph',
            field=models.ImageField(blank=True, null=True, upload_to='students/', validators=[apps.common.validators.validate_file_extension, apps.common.validators.validate_file_size]),
        ),
    ]
