
import apps.common.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homework', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='homework',
            name='attachment',
            field=models.FileField(blank=True, null=True, upload_to='homework/', validators=[apps.common.validators.validate_file_extension, apps.common.validators.validate_file_size]),
        ),
        migrations.AlterField(
            model_name='homeworksubmission',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='homework_submissions/', validators=[apps.common.validators.validate_file_extension, apps.common.validators.validate_file_size]),
        ),
    ]
