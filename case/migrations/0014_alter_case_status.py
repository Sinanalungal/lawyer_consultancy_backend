# Generated by Django 5.1 on 2024-09-17 07:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0013_remove_allotedcases_case_model_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='case',
            name='status',
            field=models.CharField(choices=[('Pending', 'Pending'), ('Accepted', 'Accepted'), ('Outdated', 'Outdated')], default='Pending', max_length=50),
        ),
    ]
