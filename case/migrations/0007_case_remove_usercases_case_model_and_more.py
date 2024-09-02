# Generated by Django 4.0 on 2024-08-29 06:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('case', '0006_usercases_paid'),
    ]

    operations = [
        migrations.CreateModel(
            name='Case',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_time', models.DateTimeField(auto_now_add=True)),
                ('updated_time', models.DateTimeField(auto_now=True)),
                ('case_type', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('status', models.CharField(max_length=50)),
                ('date_applied', models.DateField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='usercases',
            name='case_model',
        ),
        migrations.RemoveField(
            model_name='usercases',
            name='user',
        ),
        migrations.DeleteModel(
            name='CaseModels',
        ),
        migrations.DeleteModel(
            name='UserCases',
        ),
    ]