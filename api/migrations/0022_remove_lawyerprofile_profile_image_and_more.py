# Generated by Django 4.0 on 2024-07-26 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0021_remove_customuser_departments_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='lawyerprofile',
            name='profile_image',
        ),
        migrations.AddField(
            model_name='customuser',
            name='profile_image',
            field=models.ImageField(blank=True, null=True, upload_to='profile/'),
        ),
    ]
