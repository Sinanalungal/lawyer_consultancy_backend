# Generated by Django 4.0 on 2024-06-14 10:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='thread',
            name='is_listed',
            field=models.BooleanField(default=True),
        ),
    ]
