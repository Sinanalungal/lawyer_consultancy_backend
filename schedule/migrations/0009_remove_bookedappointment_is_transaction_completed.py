# Generated by Django 5.1 on 2024-09-20 14:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0008_paymentdetails_payment_for'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bookedappointment',
            name='is_transaction_completed',
        ),
    ]
