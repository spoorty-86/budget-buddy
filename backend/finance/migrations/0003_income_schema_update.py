from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('finance', '0002_default_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='income',
            name='title',
            field=models.CharField(default='', max_length=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='income',
            name='updated_at',
            field=models.DateTimeField(default=django.utils.timezone.now, auto_now=True),
            preserve_default=False,
        ),
        migrations.RenameField(
            model_name='income',
            old_name='date_received',
            new_name='income_date',
        ),
        migrations.RenameField(
            model_name='income',
            old_name='notes',
            new_name='description',
        ),
        migrations.AlterField(
            model_name='income',
            name='source',
            field=models.CharField(choices=[('SALARY', 'Salary'), ('POCKET_MONEY', 'Pocket Money'), ('SCHOLARSHIP', 'Scholarship'), ('FREELANCING', 'Freelancing'), ('BUSINESS', 'Business'), ('OTHER', 'Other')], max_length=20),
        ),
    ]
