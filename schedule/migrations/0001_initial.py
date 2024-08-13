# Generated by Django 4.0 on 2024-08-13 04:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Scheduling',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('start_time', models.TimeField()),
                ('end_time', models.TimeField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=6)),
                ('reference_until', models.DateField()),
            ],
        ),
    ]