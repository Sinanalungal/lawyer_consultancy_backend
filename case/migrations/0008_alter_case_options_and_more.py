# Generated by Django 4.0 on 2024-08-29 14:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0024_lawyerprofile_address_lawyerprofile_city_and_more'),
        ('case', '0007_case_remove_usercases_case_model_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='case',
            options={'ordering': ['-created_time']},
        ),
        migrations.RenameField(
            model_name='case',
            old_name='date_applied',
            new_name='reference_until',
        ),
        migrations.AddField(
            model_name='case',
            name='budget',
            field=models.PositiveIntegerField(default=2),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='case',
            name='user',
            field=models.ForeignKey(default=2, on_delete=django.db.models.deletion.CASCADE, to='api.customuser'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='case',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Accepted', 'Accepted')], default='Pending', max_length=50),
        ),
    ]