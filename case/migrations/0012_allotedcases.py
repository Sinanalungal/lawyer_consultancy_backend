# Generated by Django 5.1 on 2024-08-31 08:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0028_alter_lawyerprofile_state'),
        ('case', '0011_selectedcases_created_at'),
    ]

    operations = [
        migrations.CreateModel(
            name='AllotedCases',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('Ongoing', 'Ongoing'), ('Completed', 'Completed')], default='Ongoing', max_length=50)),
                ('case_model', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='case.case')),
                ('lawyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='api.lawyerprofile')),
            ],
        ),
    ]
