
import apps.common.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('admissions', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='admissiondocument',
            name='file',
            field=models.FileField(upload_to='admissions/', validators=[apps.common.validators.validate_file_extension, apps.common.validators.validate_file_size]),
        ),
    ]
