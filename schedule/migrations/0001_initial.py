# Generated by Django 4.0 on 2024-08-15 18:04

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('api', '0024_lawyerprofile_address_lawyerprofile_city_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Scheduling',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=6)),
                ('reference_until', models.DateField()),
                ('is_listed', models.BooleanField(default=True)),
                ('is_canceled', models.BooleanField(default=False)),
                ('lawyer_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.lawyerprofile')),
            ],
        ),
        migrations.CreateModel(
            name='BookedAppointment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('session_date', models.DateTimeField(blank=True, default=None, null=True)),
                ('booked_at', models.DateTimeField(auto_now_add=True)),
                ('is_completed', models.BooleanField(default=False)),
                ('is_canceled', models.BooleanField(default=False)),
                ('scheduling', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='schedule.scheduling')),
                ('user_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.customuser')),
            ],
        ),
    ]
