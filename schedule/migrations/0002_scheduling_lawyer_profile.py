# Generated by Django 4.0 on 2024-08-13 05:09

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0024_lawyerprofile_address_lawyerprofile_city_and_more'),
        ('schedule', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='scheduling',
            name='lawyer_profile',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='api.lawyerprofile'),
            preserve_default=False,
        ),
    ]
