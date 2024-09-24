# Generated by Django 5.1 on 2024-09-23 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0009_remove_bookedappointment_is_transaction_completed'),
    ]

    operations = [
        migrations.RenameField(
            model_name='bookedappointment',
            old_name='session_date',
            new_name='session_end',
        ),
        migrations.AddField(
            model_name='bookedappointment',
            name='session_start',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]