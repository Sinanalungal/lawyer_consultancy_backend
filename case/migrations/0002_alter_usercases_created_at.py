# Generated by Django 4.0 on 2024-06-24 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usercases',
            name='created_at',
            field=models.DateTimeField(auto_now=True),
        ),
    ]