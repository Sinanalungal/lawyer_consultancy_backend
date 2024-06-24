# Generated by Django 4.0 on 2024-06-24 04:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('api', '0018_alter_customuser_departments_alter_customuser_groups_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CaseModels',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('is_listed', models.BooleanField(default=True)),
                ('department', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.department')),
                ('lawyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.customuser')),
            ],
        ),
    ]
