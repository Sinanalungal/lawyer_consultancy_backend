# Generated by Django 4.0 on 2024-08-30 07:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0027_alter_lawyerprofile_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lawyerprofile',
            name='state',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
