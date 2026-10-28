
import apps.common.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teachers', '0002_teacher_staff_category_teacher_teaching_level_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='teacher',
            name='cnic',
            field=models.CharField(blank=True, db_index=True, help_text='Format: XXXXX-XXXXXXX-X (Pakistani CNIC). Unique per teacher.', max_length=20, unique=True),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='gender',
            field=models.CharField(choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')], default='male', max_length=10),
        ),
        migrations.AlterField(
            model_name='teacher',
            name='photograph',
            field=models.ImageField(blank=True, null=True, upload_to='teachers/', validators=[apps.common.validators.validate_file_extension, apps.common.validators.validate_file_size]),
        ),
    ]
